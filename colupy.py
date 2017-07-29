import requests
import json
import pandas as pd
import time

from plotly.offline import iplot, plot
import plotly.tools as tls

from plotly.graph_objs import Scatter, Line, Marker, Figure, Data, Layout, XAxis, YAxis, Scattergl

import networkx as nx

def getFromApi(colu_url = 'https://api.coloredcoins.org/v3/', 
               api_endpoint = '', param = '', verbose = False, wait = 0):
    if verbose:
        print 'Get from:'+api_endpoint+'/'+param + ' waiting', wait
    response = requests.get(colu_url+api_endpoint+'/'+param)
    time.sleep(wait)
    return response

class Asset:
    def __init__(self, assetId = None, colu_url = 'https://api.coloredcoins.org/v3/', asset_dict = None, asset_file = None):
        '''initializes with the assetId by querying blockchain'''
        self.colu_url = colu_url
        self.someUtxo = None
        self.metadata = None
        self.stakeholders = None
        
        if asset_file is not None:
            with open(asset_file, 'r') as f:
                asset_dict = json.load(f)
                
        if asset_dict is None:
            self.assetId = assetId
        else:
            self.load_asset(asset_dict)
    
        
    def get_stakeholders(self, wait = .1, verbose = False):
        '''Queries api for stakeholders, but response includes some other useful asset metadata'''
        if self.stakeholders is not None:
            return self.stakeholders['holders']
        
        response = getFromApi(colu_url = self.colu_url,
                              api_endpoint='stakeholders',
                              param = self.assetId, 
                              wait = wait,
                              verbose = verbose).json() 
        
        assert(self.assetId == response['assetId'])     

        self.someUtxo = response['someUtxo'] # needed to access asset-specific metadata?
        self.stakeholders = response
        return self.stakeholders['holders']
        
    def get_metadata(self, use_utxo = False, utxo = None, force = False, wait = .1, verbose = False):
        '''Get metadata for this asset. If use_utxo is True, will get utxo-specific metdata,
        using either utxo as input or some utxo taken from existing holders. If force is True,
        will not use cached metadata.'''
        
        if (self.metadata is not None) & (not force):
            return self.metadata
        
        if use_utxo:
            if utxo is None:
                if self.someUtxo is None:
                    self.get_stakeholders()
                utxo = self.someUtxo
            response = getFromApi(colu_url = self.colu_url,
                                  api_endpoint = 'assetmetadata',
                                  param = self.assetId+'/'+utxo,
                                  wait = wait,
                                  verbose = verbose).json()
        else:
            response = getFromApi(colu_url = self.colu_url,
                                  api_endpoint = 'assetmetadata',
                                  param = self.assetId, 
                                  wait = wait,
                                  verbose = verbose).json()
            
        self.metadata = response        
        return self.metadata
    
    def as_dict(self):
        return dict(assetId = self.assetId,
                    someUtxo = self.someUtxo,
                    metadata = self.metadata,
                    stakeholders = self.stakeholders)
    
    def load_asset(self, asset_dict):
        self.assetId = asset_dict['assetId']
        self.someUtxo = asset_dict['someUtxo']
        self.metadata = asset_dict['metadata']
        self.stakeholders = asset_dict['stakeholders']
    
    def as_json(self, **kwargs):
        return json.dumps(self.as_dict(), **kwargs)

    def save(self, filename):
        with open(filename, 'w') as f:
            f.write(self.as_json(indent = 2))

class Holder:
    def __init__(self, address = None, colu_url = 'https://api.coloredcoins.org/v3/', holder_dict = None, holder_file = None):
        self.colu_url = colu_url
        self.utxos = None
        self.assets = None
        self.address_info = None

        if holder_file is not None:
            with open(holder_file, 'r') as f:
                holder_dict = json.load(f)

        if holder_dict is None:
            self.address = address
        else:
            self.load_holder(holder_dict)
        
    def get_address_info(self, wait = .1):
        if self.address_info is not None:
            return self.address_info
        
        self.address_info = getFromApi(colu_url = self.colu_url, 
                              api_endpoint='addressinfo',
                              param=self.address,
                              wait = wait).json()
        return self.address_info
    
    def get_utxos(self, wait = .1):
        if self.utxos is not None:
            return self.utxos
        
        address_info = self.get_address_info(wait)
        
        assert(self.address == address_info['address'])
        self.utxos = address_info['utxos']
        
        return self.utxos
    
    def get_assets(self, wait = .1):
        if self.assets is not None:
            return self.assets
        
        utxos = pd.DataFrame(self.get_utxos(wait))
        copy_properties = ['blockheight','blocktime', 'used', 'value']
        asset_group = []
        for i,assets in utxos.assets.iteritems():
            if len(assets) > 0:
                asset_frame = pd.DataFrame(assets)
                for c in copy_properties:
                    asset_frame.loc[:,c] = utxos.loc[i,c]
                asset_group.append(asset_frame)

        self.assets = pd.concat(asset_group, ignore_index=True)
        return self.assets
    
    def as_dict(self):
        return dict(address = self.address,
                    address_info = self.address_info)
        
    def load_holder(self,holder_dict):
        self.address = holder_dict['address']
        self.address_info = holder_dict['address_info']
        self.get_utxos()
        self.get_assets()
        
    def as_json(self, **kwargs):
        return json.dumps(self.as_dict(), **kwargs)

    def save(self, filename, **json_kwargs):
        with open(filename, 'w') as f:
            f.write(self.as_json(**json_kwargs))


class Colu:
    '''Provides high-level access to colu REST api while avoiding extraneous requests.'''
    def __init__(self, colu_url = 'https://api.coloredcoins.org/v3/', colu_dict = None, colu_file = None):
        '''If colu_file is specified as json, will load assets and holders, ignoring colu_dict
        '''
        self.colu_url = colu_url
        self._loaded = None 
        self._search_set = None

        if colu_file is not None:
            with open(colu_file, 'r') as f:
                colu_dict = json.load(f)
            
        if colu_dict is None:
            self.assets = {}
            self.holders = {}
        else:
            self.load_colu(colu_dict)
    
    def as_dict(self):
        return dict(assets = dict((k,v.as_dict()) for k,v in self.assets.iteritems()),
                    holders = dict((k,v.as_dict()) for k,v in self.holders.iteritems()))
    
    def as_json(self, **kwargs):
        return json.dumps(self.as_dict(), **kwargs)
    
    def load_colu(self,colu_dict):
        self.assets = dict((k, Asset(colu_url = self.colu_url, asset_dict = v)) 
                           for k,v in colu_dict['assets'].iteritems())
        self.holders = dict((k, Holder(colu_url = self.colu_url, holder_dict = v)) 
                            for k,v in colu_dict['holders'].iteritems())
    
    def get_asset(self, assetId, force = False, verbose = False, asset_dict = None):
        if (not self.assets.has_key(assetId)) | force:
            if verbose: 
                print 'getting asset for', assetId
            self.assets[assetId] = Asset(assetId, colu_url = self.colu_url, asset_dict = asset_dict)
        
        return self.assets[assetId]

    def get_holder(self, address, force = False, verbose = False, holder_dict = None):
        if (not self.holders.has_key(address)) | force:
            if verbose: print 'getting holder for', address
            self.holders[address] = Holder(address, self.colu_url, holder_dict)
        
        return self.holders[address]
    
    def crawl_assets(self, assetIds, n = 5, wait = 0, verbose = False):
        '''Starting from each assetId, find holders of that asset, then interatively search their assets for more

        assetIds must be iterable'''
        if self._loaded is None:
            self._loaded = set()

        if self._search_set is None:
            self._search_set = set(assetIds)

        
        while (n > 0) & (len(self._search_set) > 0):
            assetId = self._search_set.pop()
            
            if verbose:
                print assetId, n
            asset = self.get_asset(assetId)
            self._loaded.add(assetId)
            stakeholders = pd.DataFrame(asset.get_stakeholders(wait))

            for address in stakeholders.address:
                holder = self.get_holder(address)
                holder_assets = holder.get_assets(wait).assetId.values
                for a in holder_assets:
                    self.get_asset(a)
                    if a not in self._loaded: 
                        self._search_set.add(a)

            if verbose:
                for a_ in self._search_set: 
                    print '\t',a_
            n = n-1
        return self._loaded
    
    def save(self, filename):
        with open(filename, 'w') as f:
            f.write(self.as_json(indent = 2))

    def get_asset_graph(self, min_assets = 1):
        self.graph = nx.Graph()
        for assetId in self.assets:
            self.graph.add_node(assetId, isasset = True)

        for address in self.holders.keys():
            if len(self.holders[address].get_assets()) >= min_assets:
                self.graph.add_node(address, isasset = False)

    def weight_assets(self, min_assets = 1):
        for address, holder in self.holders.iteritems():
            if len(self.holders[address].get_assets()) >= min_assets:
                holder.assets = holder.assets.assign(totalSupply = [self.assets[assetId].get_metadata()['totalSupply'] 
                                                                    for assetId in holder.assets.assetId])
                holder.assets = holder.assets.assign(weight = holder.assets.amount/holder.assets.totalSupply)
#                 weighted_edges = [(assetId, address, weight) for assetId, weight in holder.assets[['assetId','weight']].itertuples(index = False)]
                for assetId, weight in holder.assets[['assetId','weight']].itertuples(index = False):
                    self.graph.add_edge(address, assetId, weight = weight)
#                 self.graph.add_weighted_edges_from(weighted_edges)