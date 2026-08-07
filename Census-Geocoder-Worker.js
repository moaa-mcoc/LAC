// LAC Census Geocoder Proxy — Cloudflare Worker
//
// Forwards address lookups to the Census Bureau Geocoder
// (geocoding.geo.census.gov) and adds CORS headers so action.html can call
// it directly from the browser. The Census API itself is free and requires
// no key — this Worker exists only to add the Access-Control-Allow-Origin
// header the Census API doesn't send, which browsers require for
// cross-origin fetch() calls to read the response.
//
// Deploy: Cloudflare dashboard → Workers & Pages → Create → Create Worker
// → paste this in → Deploy. Copy the resulting *.workers.dev URL (or map a
// custom route) and send it back — it goes into the CENSUS_GEOCODER_URL
// constant in action.html.

const ALLOWED_ORIGINS = [
  'https://moaa-mcoc.github.io',
];

const CENSUS_BASE = 'https://geocoding.geo.census.gov/geocoder/geographies/onelineaddress';

function corsHeaders(origin) {
  const allowOrigin = ALLOWED_ORIGINS.includes(origin) ? origin : ALLOWED_ORIGINS[0];
  return {
    'Access-Control-Allow-Origin': allowOrigin,
    'Access-Control-Allow-Methods': 'GET, OPTIONS',
    'Access-Control-Allow-Headers': 'Content-Type',
    'Vary': 'Origin',
  };
}

export default {
  async fetch(request) {
    const origin = request.headers.get('Origin') || '';
    const headers = corsHeaders(origin);

    if (request.method === 'OPTIONS') {
      return new Response(null, { headers });
    }

    const incoming = new URL(request.url);
    const address = incoming.searchParams.get('address');
    if (!address) {
      return new Response(JSON.stringify({ error: 'Missing address parameter' }), {
        status: 400,
        headers: { ...headers, 'Content-Type': 'application/json' },
      });
    }

    const censusUrl = new URL(CENSUS_BASE);
    censusUrl.searchParams.set('address', address);
    censusUrl.searchParams.set('benchmark', 'Public_AR_Current');
    censusUrl.searchParams.set('vintage', 'Current_Current');
    censusUrl.searchParams.set('format', 'json');

    try {
      // Cache successful lookups for 5 minutes — cuts repeat calls to the
      // Census API for the same address and keeps this comfortably inside
      // the Workers free tier even on a busy advocacy day.
      const resp = await fetch(censusUrl.toString(), {
        cf: { cacheTtl: 300, cacheEverything: true },
      });
      const body = await resp.text();
      return new Response(body, {
        status: resp.status,
        headers: { ...headers, 'Content-Type': 'application/json' },
      });
    } catch (err) {
      return new Response(JSON.stringify({ error: 'Upstream geocoder request failed' }), {
        status: 502,
        headers: { ...headers, 'Content-Type': 'application/json' },
      });
    }
  },
};
