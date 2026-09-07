import { defineConfig } from 'astro/config';
import sitemap from '@astrojs/sitemap';

export default defineConfig({
  site: 'https://gekijo-tobira.com',
  output: 'static',
  // 本番（Cloudflare Pages）が末尾スラッシュありへ308リダイレクトするため always に合わせる
  trailingSlash: 'always',
  integrations: [
    sitemap({
      // 検索結果に出す必要のないページは除外する
      filter: (page) => !page.includes('/contact-thanks'),
      changefreq: 'monthly',
      lastmod: new Date(),
    }),
  ],
});
