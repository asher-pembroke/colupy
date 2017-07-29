import unittest

from colupy import Asset, Holder, Colu

class Test_Asset(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
    	print 'setting up romanian_votecoin asset'
        # Romanian votecoin from bitnation
    	assetId = 'Ua7qAZa2UQioKf4Z4KKFwgpzUug3Ztczm7YgE4' 
    	cls._asset = Asset(asset_file = 'testdata/' + assetId + '.json')
        cls._asset.get_metadata(use_utxo=True, verbose = True)

    @classmethod
    def tearDownClass(cls):
    	print 'tear down'

    def test_load_metdata(self):
    	metadata = self._asset.get_metadata()
    	self.assertEquals(metadata['firstBlock'], 456384)

    def test_loading_assets(self):
        # test loaded assets
        assetId = 'Ua7qAZa2UQioKf4Z4KKFwgpzUug3Ztczm7YgE4'
        loaded_asset = Asset(asset_file= 'testdata/' + assetId + '.json')
        loaded_asset_dict = loaded_asset.as_dict()
        romanian_votecoin_dict = self._asset.as_dict()
        for k,v in romanian_votecoin_dict.items():
            self.assertEquals(v, loaded_asset_dict[k])

    def test_loading_dictionary(self):
        romanian_votecoin_dict = self._asset.as_dict()
        loaded_asset_dict = Asset(asset_dict=romanian_votecoin_dict).as_dict()
        for k,v in romanian_votecoin_dict.items():
            self.assertEquals(v, loaded_asset_dict[k])


class Test_Holder(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        print 'setting up asset holder'
        cls._holderId = '1KmyHAn4LbtJqykkSi8phfRZy7FMwu4zQk'
        cls._holder = Holder(holder_file = 'testdata/' + cls._holderId + '.json')

    def test_loading_as_dict(self):
        holder_dict = self._holder.as_dict()
        loaded_asset_dict = Holder(holder_dict = holder_dict).as_dict()

        for k,v in loaded_asset_dict.items():
            self.assertEquals(v, loaded_asset_dict[k])

    def test_holder_assets(self):
        print len(self._holder.get_assets())


class Test_colu_crawler(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        print 'setting up colu crawler'
        cls._colu = Colu(colu_file = 'testdata/colu_save.json')

    def test_new_asset(self):
        # Romanian votecoin from bitnation
        assetId = 'Ua7qAZa2UQioKf4Z4KKFwgpzUug3Ztczm7YgE4' 
        romanian_votecoin = self._colu.get_asset(assetId, verbose=True)
        self.assertNotEquals(romanian_votecoin, self._colu.get_asset(assetId, force = True, verbose = True))


    def test_colu_dict(self):
        colu_dict = self._colu.as_dict()
        loaded_colu_dict = Colu(colu_dict = colu_dict).as_dict()

        for k,v in loaded_colu_dict.iteritems():
            print k,v
            self.assertEquals(colu_dict[k], v)

if __name__ == '__main__':
	unittest.main()