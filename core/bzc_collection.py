from bson import json_util
from collections import defaultdict
from core.utils import WebSession, writeFile, readFile, writeJsonFile, readJsonFile

rpc_url = 'https://polygon-rpc.com'
abi_url = 'https://api.polygonscan.com/api?module=contract&action=getabi&address='

class BzcCollection():
    def __init__(self):
        self._web3 = None
        self._session = WebSession()

        self.metadata = {}
        self.ranks = {}
        self.offers = {}

    @property
    def web3(self):
        from web3 import Web3
        if not self._web3:
            self._web3 = Web3(Web3.HTTPProvider(rpc_url))
        return self._web3

    def rank_and_offers(self):
        self.get_metadata()
        self.rank_collection()
        self.offers()

    def get_floor_price(self, collection_name, type):
        return ""

    # Pull offers and store, sorted by price
    def offers(self):
        for collection_name, coll_data in collections.items():
            # Files created by nodejs scrape of opensea
            filename = f"data/{collection_name}_offers.json";
            if os.path.exists(filename):
                offers = readJsonFile(filename)
                self.offers[collection_name] = offers
                # for offer in offers:

                    #  \
                    #         and self.ranks[collection_name][offer['tokenId']]['rank'] < collections[collection_name][
                    #     'quantity'] / 4:
                    #     print(
                    #         f"{collection_name} rank: {self.ranks[collection_name][offer['tokenId']]['rank']}, {offer['floorPrice']['amount']}, {offer['offerUrl']} ")

    # Get the function definitions for the polygon contract
    def get_abi(self, collection_name):
        contract = collections[collection_name]['contract']

        ABI_ENDPOINT = f"{abi_url}{contract}"
        response = self._session.get_url(ABI_ENDPOINT, cache_expire=-1, return_response=True)

        try:
            abi = json.loads(response.json()['result'])
        except Exception as e:
            # Some contracts havent been verified... just pull the genesis contract, which has the same get uri def
            abi = self.get_abi("billionairezombiesclub")
        return abi

    # get the ipfs url that points to the meta data
    def get_token_uri(self, collection_name, token_id, cache=False):
        if cache:
            cache_file = f'{WebSession.TempDir}{collection_name}_{token_id}_get_token_uri.cache'

            if os.path.exists(cache_file):
                return readFile(cache_file)

        insecure = True

        abi = self.get_abi(collection_name)

        contract = collections[collection_name]['contract']

        if insecure:
            contract = Web3.toChecksumAddress(contract)
        token_contract = self.web3.eth.contract(abi=abi, address=contract)

        uri = token_contract.functions.tokenURI(token_id).call()

        if cache:
            writeFile(cache_file, uri)

        return uri

    # get all the metadata for each item
    def get_metadata(self, refresh=False):
        if not refresh and os.path.exists(f"data/metadata.json"):
            self.metadata = readJsonFile(f"data/metadata.json")
            return

        self.metadata = defaultdict(dict)
        for collection_name, coll_data in collections.items():
            if coll_data['metadata_type'] == 'generative':
                ipfs_uri = self.get_token_uri(collection_name, 1).replace("://", "/")
                for token_id in range(1, collections[collection_name]['quantity'] + 1):
                    try:
                        url = "https://mygateway.mypinata.cloud/" + f"{ipfs_uri.replace('1.json', str(token_id))}.json"
                        meta = self._session.get_url(url, cache_expire=-1)
                        self.metadata[collection_name][token_id] = meta
                        if token_id % 50 == 0:
                            print(
                                f'{collection_name} Fetching metadata {token_id}/{collections[collection_name]["quantity"]}')
                    except Exception as e:
                        pass
                    continue
            elif coll_data['metadata_type'] == 'item':
                for token_id in range(1, collections[collection_name]['quantity'] + 1):
                    try:
                        # ipfs_uri repeats per type
                        ipfs_uri = self.get_token_uri(collection_name, token_id, cache=True).replace("://", "/")
                        url = "https://mygateway.mypinata.cloud/" + ipfs_uri
                        meta = self._session.get_url(url, cache_expire=-1)
                        self.metadata[collection_name][token_id] = meta
                        if token_id % 50 == 0:
                            print(f'Fetching metadata {token_id}/{collections[collection_name]["quantity"]}')
                    except Exception as e:
                        pass
                    continue
        writeJsonFile(f"data/metadata.json", self.metadata)

    # Rank each collection
    def rank_collection(self, refresh=False, use_num_traits=True):
        if not refresh and os.path.exists(f"data/ranks.json"):
            self.ranks = readJsonFile(f"data/ranks.json")
            return

        self.ranks = defaultdict(dict)
        for collection_name, metadata in self.metadata.items():
            traits_total = defaultdict(lambda: defaultdict(int))
            for token_id, data in metadata.items():
                for trait in data['attributes']:
                    traits_total[trait['trait_type']][trait['value']] += 1

                if use_num_traits:
                    traits_total["NumTraits"][str(len(data['attributes']))] += 1
                    data['attributes'].append({'trait_type': "NumTraits", 'value': str(len(data['attributes']))})

            scores = {}
            total = len(metadata)
            for token_id, data in metadata.items():
                score = 0
                trait_text = ''
                for trait in data['attributes']:
                    score += 1 / (traits_total[trait['trait_type']][trait['value']] / total)
                    trait_text += f'{trait["trait_type"]}:{trait["value"]}-%{traits_total[trait["trait_type"]][trait["value"]] / total * 100:.2f},'

                trait_text += f', Traits: {len(data["attributes"])}'
                scores[token_id] = {'score': score, 'trait_text': trait_text}

            scores = {k: v for k, v in sorted(scores.items(), key=lambda item: item[1]['score'], reverse=True)}

            rank = 1
            for token_id, data in scores.items():
                data['rank'] = rank
                rank += 1

            self.ranks[collection_name] = scores

        writeJsonFile(f"data/ranks.json", self.ranks)