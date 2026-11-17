import { getAssetFromKV } from '@cloudflare/kv-asset-handler';
import manifestJSON from '__STATIC_CONTENT_MANIFEST';

const assetManifest = JSON.parse(manifestJSON);

export default {
  async fetch(request, env, ctx) {
    try {
      return await getAssetFromKV(
        { request, waitUntil: ctx.waitUntil.bind(ctx) },
        {
          ASSET_NAMESPACE: env.__STATIC_CONTENT,
          ASSET_MANIFEST: assetManifest,
        }
      );
    } catch (e) {
      // If the asset is not found, try to serve index.html
      try {
        const notFoundUrl = new URL(request.url);
        notFoundUrl.pathname = '/index.html';
        return await getAssetFromKV(
          { request: new Request(notFoundUrl, request), waitUntil: ctx.waitUntil.bind(ctx) },
          {
            ASSET_NAMESPACE: env.__STATIC_CONTENT,
            ASSET_MANIFEST: assetManifest,
          }
        );
      } catch (e2) {
        return new Response('Not Found', { status: 404 });
      }
    }
  },
};
