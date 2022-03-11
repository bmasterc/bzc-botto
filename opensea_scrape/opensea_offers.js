require('log-timestamp');
const { getSystemErrorMap } = require("util");

const options = {
  debug: false,
  logs: true,
  sort: true,
  browserInstance: undefined,
}

os_collection_names = ["billionairezombiesclub","bzc-metaverse","skeleton-kings","bzc-skeleton-keys","bzc-metacrystals","bzc-skeleton-keys-3d"]

pull_opensea__collection_offers_matic();

async function pull_opensea__collection_offers_matic() {
  for (os_collection_name of os_collection_names)
    try {
      await pull_opensea_offers_matic(os_collection_name);
    } catch (error) {
      console.log(error.stack)
    }
}

async function pull_opensea_offers_matic(os_collection_name) {
  console.log(`PROCESSING OS COLLECTION ${os_collection_name}`);
  const fs = require('fs');
  const puppeteer = require('puppeteer-extra');
  const StealthPlugin = require('puppeteer-extra-plugin-stealth');

  filename = `../data/${os_collection_name}_offers.json`;
  url = `https://opensea.io/collection/${os_collection_name}?search[sortAscending]=true&search[sortBy]=PRICE&search[toggles][0]=BUY_NOW`;

  puppeteer.use(StealthPlugin());

  browser = await puppeteer.launch({
    headless: !options.debug,
    args: ['--start-maximized'],
  });
  page = await browser.newPage();

  scrapedAjaxOffers = [];
  offers = [];
  // finished = false;

  page.on('response', async(response) => {
    try {
      const request = response.request();
      if (request.url().indexOf('api.opensea.io') !== -1){
          if (request.method() == 'POST') {
            req = JSON.parse(request.postData())
            if (req.id == 'AssetSearchQuery') {
              resp = await response.json()
              // finished = !resp.data.query.search.pageInfo.hasNextPage
              scrapedAjaxOffers.push(...resp.data.query.search.edges)
              console.log(`Added ${resp.data.query.search.edges.length + scrapedAjaxOffers.length + offers.length} / ${resp.data.query.search.totalCount}`);
            }
          }
      }
    } catch (error) {
          console.log(error.stack)
        }
  })

  await page.goto(url);
  
  // page.on('console', (log) => 
  // console[log._type](`bLog: ${log._text}`));

  i = 0
  function sleep(ms) {
    return new Promise((resolve) => {
      setTimeout(resolve, ms);
    });
  }

  //Begin code stolen frpm opensea-scraper
  function _extractOffers(__wired__, { sort = true } = {}) {
    // create currency dict to extract different offer currencies
    const currencyDict = {};
    Object.values(__wired__.records)
      .filter(o => o.__typename === "AssetType")
      .filter(o => o.usdSpotPrice)
      .forEach(currency => {
        currencyDict[currency.id] = {
          id: currency.id,
          symbol: currency.symbol,
          imageUrl: currency.imageUrl,
          usdSpotPrice: currency.usdSpotPrice,
        }
      });
  
    // create contract dict to generate offerUrl
    const assetContractDict = {};
    Object.values(__wired__.records)
      .filter(o => o.__typename === "AssetContractType" && o.address)
      .forEach(o => {
        assetContractDict[o.id] = o.address;
      })
  
    // get all floorPrices (all currencies)
    const floorPrices = Object.values(__wired__.records)
      .filter(o => o.__typename === "AssetQuantityType")
      .filter(o => o.quantityInEth)
      .map(o => {
        return {
          amount: o.quantity / 1000000000000000000,
          currency: currencyDict[o.asset.__ref].symbol,
        }
      });
  
    // get offers
    const offers = Object.values(__wired__.records)
      .filter(o => o.__typename === "AssetType" && o.tokenId)
      .map(o => {
        const assetContract = _extractAssetContract(o, assetContractDict);
        const tokenId = o.tokenId;
        const contractAndTokenIdExist = Boolean(assetContract) && Boolean(tokenId);
        return {
          name: o.name,
          tokenId: tokenId,
          displayImageUrl: o.displayImageUrl,
          assetContract: assetContract,
          offerUrl: contractAndTokenIdExist ? `https://opensea.io/assets/matic/${assetContract}/${tokenId}` : undefined,
        };
      });
  
    // merge information together:
    floorPrices.forEach((floorPrice, indx) => {
      offers[indx].floorPrice = floorPrice;
    });
  
    return offers;
  }
  function _extractAssetContract(offerObj, assetContractDict) {
    try {
      return assetContractDict[offerObj.assetContract.__ref];
    } catch (err) {
      return undefined;
    }
  }
  let key = await page.evaluate(() => { return window.__wired__;});
  offers = _extractOffers(key)
  //End code stolen
  console.log(`Added ${offers.length} embedded in page`)

  //close popup
  grid_button = await page.$x("//i[@value='apps']")
  await grid_button[0].click()

  await page.evaluate(() => new Promise((resolve) => {
      let currentScrollTop = -1;
      const interval = setInterval(() => {
        window.scrollBy(0, 50);
        
        const endOfPageReached = document.documentElement.scrollTop === currentScrollTop;
  
        if(!endOfPageReached) {
          currentScrollTop = document.documentElement.scrollTop;
          return;
        }
        console.error(`Done Scrolling...`);
        clearInterval(interval);
        resolve(true)
      }, 120);
    }));

  await browser.close();

  for (off of scrapedAjaxOffers) {
    offers.push({assetContract: off.node.asset.assetContract.address, displayImageUrl: off.node.asset.imageUrl, 
      floorPrice: {amount: (off.node.asset.orderData.bestAsk? off.node.asset.orderData.bestAsk.paymentAssetQuantity.quantity/10**18: null)},
      name: off.node.asset.name, tokenId: off.node.asset.tokenId, 
      offerUrl: `https://opensea.io/assets/matic/${off.node.asset.assetContract.address}/${off.node.asset.tokenId}`
    })	
  }

  fs.writeFileSync(filename, JSON.stringify(offers));
  console.log(`Wrote ${offers.length} to ${filename}`)
}