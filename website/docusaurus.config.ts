import type {Config} from '@docusaurus/types';
import type * as Preset from '@docusaurus/preset-classic';

const config: Config = {
  title: 'pyredsql',
  tagline: 'Format and extract Redshift SQL embedded in Python files.',
  favicon: 'img/favicon.svg',

  url: 'https://enumura1.github.io',
  baseUrl: '/pyredsql/',

  organizationName: 'enumura1',
  projectName: 'pyredsql',

  onBrokenLinks: 'throw',
  markdown: {
    hooks: {
      onBrokenMarkdownLinks: 'warn',
    },
  },

  i18n: {
    defaultLocale: 'en',
    locales: ['en'],
  },

  presets: [
    [
      'classic',
      {
        docs: {
          sidebarPath: './sidebars.ts',
          editUrl: 'https://github.com/enumura1/pyredsql/tree/main/website/',
        },
        blog: false,
        theme: {
          customCss: './src/css/custom.css',
        },
      } satisfies Preset.Options,
    ],
  ],

  themeConfig: {
    image: 'img/social-card.svg',
    navbar: {
      title: 'pyredsql',
      logo: {
        alt: 'pyredsql logo',
        src: 'img/logo.svg',
      },
      items: [
        {
          type: 'docSidebar',
          sidebarId: 'tutorialSidebar',
          position: 'left',
          label: 'Docs',
        },
        {
          href: 'https://github.com/enumura1/pyredsql',
          label: 'GitHub',
          position: 'right',
        },
      ],
    },
    footer: {
      style: 'dark',
      links: [
        {
          title: 'Docs',
          items: [
            {
              label: 'Introduction',
              to: '/docs/intro',
            },
            {
              label: 'Quick Start',
              to: '/docs/getting-started/quick-start',
            },
            {
              label: 'Safety',
              to: '/docs/project/safety',
            },
          ],
        },
        {
          title: 'Project',
          items: [
            {
              label: 'GitHub',
              href: 'https://github.com/enumura1/pyredsql',
            },
            {
              label: 'Issues',
              href: 'https://github.com/enumura1/pyredsql/issues',
            },
          ],
        },
      ],
      copyright: 'Copyright © 2026 enumura1.',
    },
    prism: {
      theme: require('prism-react-renderer').themes.github,
      darkTheme: require('prism-react-renderer').themes.dracula,
      additionalLanguages: ['python', 'sql', 'bash'],
    },
  } satisfies Preset.ThemeConfig,
};

export default config;
