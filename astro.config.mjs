import { defineConfig } from 'astro/config';

export default defineConfig({
  site: 'https://ryanjcross.com',
  redirects: {
    '/projects/stampede-sky': '/projects/sierra-space/',
    '/projects/cu-boulder': '/projects/kashmir-world-foundation/',
    '/projects/project-04': '/projects/design-build-fly/',
  },
});
