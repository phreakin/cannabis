-- =============================================================================
-- Bookmark Categories Seed — Full list (existing + new)
-- Updates descriptions on existing rows; inserts all new categories.
-- Usage:
--   python scripts/run_sql.py scripts/sql/seed_bookmark_categories.sql
--   mysql -h HOST -u USER -pPASS DATABASE < scripts/sql/seed_bookmark_categories.sql
-- =============================================================================

CREATE TABLE IF NOT EXISTS bookmark_categories (
  id          INT UNSIGNED    NOT NULL AUTO_INCREMENT,
  name        VARCHAR(100)    NOT NULL,
  slug        VARCHAR(100)    NOT NULL,
  description TEXT,
  icon        VARCHAR(255),
  color       VARCHAR(50),
  sort_order  INT             NOT NULL DEFAULT 0,
  created_at  DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at  DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  UNIQUE KEY uq_slug (slug)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- =============================================================================
-- UPDATE existing categories with revised descriptions (matched by slug)
-- =============================================================================
INSERT INTO bookmark_categories (id, name, slug, description, icon, color, sort_order) VALUES
  (132, 'Development',        'development',        'Programming and development resources',                   'fa-code fa-terminal',                'indigo',      1),
  (133, 'Design',             'design',             'Design tools and inspiration',                            'fa-palette fa-pen-ruler',            'purple',      2),
  (134, 'News',               'news',               'News and media sites',                                    'fa-newspaper fa-tower-broadcast',    'red',         3),
  (135, 'Social',             'social',             'Social media platforms',                                  'fa-users fa-comments',               'pink',        4),
  (136, 'Tools',              'tools',              'Useful online tools and utilities',                       'fa-wrench fa-screwdriver-wrench',    'orange',      5),
  (137, 'Entertainment',      'entertainment',      'Movies, music, and games',                                'fa-film fa-gamepad',                 'teal',        6),
  (138, 'Learning',           'learning',           'Educational resources and tutorials',                     'fa-graduation-cap fa-book-open',     'green',       7),
  (139, 'Shopping',           'shopping',           'E-commerce and shopping sites',                           'fa-cart-shopping fa-tags',           'yellow',      8),
  (140, 'DevOps',             'devops',             'Infrastructure, CI/CD and automation',                    'fa-server fa-gears',                 'indigo',      9),
  (141, 'Security',           'security',           'Cybersecurity and privacy resources',                     'fa-shield-halved fa-lock',           'rose',        10),
  (142, 'Networking',         'networking',         'Networking and infrastructure tools',                     'fa-network-wired fa-diagram-project','cyan',        11),
  (143, 'Databases',          'databases',          'Database systems and resources',                          'fa-database fa-table',               'emerald',     12),
  (144, 'Cloud',              'cloud',              'Cloud platforms and hosting',                             'fa-cloud fa-cloud-arrow-up',         'sky',         13),
  (145, 'APIs',               'apis',               'API documentation and integrations',                      'fa-plug fa-code-branch',             'violet',      14),
  (146, 'Photography',        'photography',        'Photography resources',                                   'fa-camera fa-image',                 'amber',       15),
  (147, 'Video',              'video',              'Video platforms and editing',                             'fa-video fa-clapperboard',           'red-pink',    16),
  (148, 'Music',              'music',              'Music streaming and audio tools',                         'fa-music fa-headphones',             'purple-blue', 17),
  (149, 'Art',                'art',                'Digital art and creative inspiration',                   'fa-palette fa-brush',                'fuchsia',     18),
  (150, 'Productivity',       'productivity',       'Productivity and workflow tools',                         'fa-check fa-list-check',             'lime',        19),
  (151, 'Documentation',      'documentation',      'Docs, references and knowledge bases',                   'fa-book fa-file-lines',              'blue-gray',   20),
  (152, 'Bookmarks',          'bookmarks',          'General saved links',                                     'fa-bookmark fa-star',                'slate',       21),
  (153, 'Projects',           'projects',           'Project management tools',                                'fa-diagram-project fa-list',         'stone',       22),
  (154, 'Finance',            'finance',            'Banking, investing and finance',                          'fa-dollar-sign fa-chart-line',       'green',       23),
  (155, 'Business',           'business',           'Business and entrepreneurship',                           'fa-briefcase fa-building',           'brown',       24),
  (156, 'Marketing',          'marketing',          'Marketing and SEO tools',                                 'fa-bullhorn fa-chart-simple',        'orange-red',  25),
  (157, 'Research',           'research',           'Research papers and references',                          'fa-microscope fa-flask',             'indigo',      26),
  (158, 'Health',             'health',             'Health and wellness resources',                           'fa-heart-pulse fa-stethoscope',      'red',         27),
  (159, 'Travel',             'travel',             'Travel planning and destinations',                        'fa-plane fa-map-location',           'cyan',        28),
  (160, 'Food',               'food',               'Recipes and food resources',                              'fa-utensils fa-bowl-food',           'amber',       29),
  (172, 'Self-Hosted',        'self-hosted',        'Self-hosted services and dashboards',                    'fa-hard-drive fa-server',            'zinc',        30),
  (173, 'HomeLab',            'homelab',            'Homelab and server management',                           'fa-microchip fa-network-wired',      'blue-green',  31),
  (174, 'Downloads',          'downloads',          'Downloads and file resources',                            'fa-download fa-folder-open',         'gray',        32),
  (161, 'Podcasts',           'podcasts',           'Podcast platforms and shows',                             'fa-podcast fa-headphones',           'purple',      33),
  (162, 'Podcast Interviews', 'podcast-interviews', 'Interview-style podcast episodes',                       'fa-microphone fa-user-tie',          'indigo',      34),
  (163, 'Tech Podcasts',      'tech-podcasts',      'Technology focused podcasts',                             'fa-headphones fa-microchip',         'blue',        35),
  (164, 'Developer Talks',    'developer-talks',    'Developer discussions and conference talks',              'fa-laptop-code fa-microphone',       'cyan',        36),
  (165, 'Audio Learning',     'audio-learning',     'Educational audio content',                               'fa-headphones fa-book-open',         'green',       37),
  (166, 'Talks & Lectures',   'talks-lectures',     'Conference talks and lectures',                           'fa-chalkboard fa-person-chalkboard', 'emerald',     38),
  (167, 'Documentaries',      'documentaries',      'Documentary videos and series',                           'fa-clapperboard fa-film',            'teal',        39),
  (168, 'Streaming',          'streaming',          'Streaming platforms and channels',                        'fa-tv fa-satellite-dish',            'rose',        40),
  (169, 'Interviews',         'interviews',         'Expert interviews and discussions',                       'fa-user-tie fa-comments',            'violet',      41),
  (170, 'Case Studies',       'case-studies',       'Real-world breakdowns and analyses',                     'fa-chart-line fa-magnifying-glass',  'amber',       42),
  (171, 'Tutorial Videos',    'tutorial-videos',    'Video tutorials and walkthroughs',                        'fa-play fa-circle-play',             'sky',         43)
ON DUPLICATE KEY UPDATE
  name        = VALUES(name),
  slug        = VALUES(slug),
  description = VALUES(description),
  icon        = VALUES(icon),
  color       = VALUES(color),
  sort_order  = VALUES(sort_order);

-- =============================================================================
-- INSERT new categories (auto-assigned IDs)
-- =============================================================================
INSERT IGNORE INTO bookmark_categories (name, slug, description, icon, color, sort_order) VALUES
  -- Video / Reactions
  ('Reactions',             'reactions',            'Reaction Videos',                                         'fa-face-smile fa-video',             'orange',      44),
  ('Car Videos',            'car-videos',           'Car Videos',                                              'fa-car fa-video',                    'maroon',      45),
  ('Baseball Videos',       'baseball-videos',      'Baseball related videos',                                 'fa-baseball fa-video',               'light-blue',  46),
  ('Toddler Videos',        'toddler-videos',       'Toddler related videos',                                  'fa-baby fa-video',                   'light-pink',  47),

  -- Tech / Dev specialties
  ('AI & ML',               'ai-ml',                'Artificial intelligence, ML, LLMs, and related tools',   'fa-brain fa-robot',                  'indigo',      48),
  ('Programming Languages', 'programming-languages','Language docs, references, and ecosystems',              'fa-code fa-book-open',               'blue',        49),
  ('PHP',                   'php',                  'PHP resources, frameworks, and tooling',                 'fa-php fa-code',                     'purple',      50),
  ('JavaScript',            'javascript',           'JavaScript resources, frameworks, and tooling',          'fa-js fa-code',                      'yellow',      51),
  ('Python',                'python',               'Python resources, packages, and tooling',                'fa-python fa-code',                  'green',       52),
  ('Web Development',       'web-development',      'Web dev resources (HTML/CSS/JS, frameworks)',            'fa-globe fa-code',                   'cyan',        53),
  ('Back-End',              'back-end',             'Server-side development and architecture',                'fa-server fa-database',              'slate',       54),
  ('Front-End',             'front-end',            'UI, CSS, frameworks, and front-end tooling',             'fa-laptop-code fa-object-group',     'sky',         55),
  ('Mobile',                'mobile',               'Mobile development resources and apps',                  'fa-mobile-screen-button fa-tablet-screen-button','teal',56),
  ('Open Source',           'open-source',          'Open-source projects and communities',                   'fa-code-branch fa-users',            'emerald',     57),
  ('Git & Version Control', 'git',                  'Git, workflows, and version control',                    'fa-code-branch fa-clock-rotate-left','orange',      58),
  ('Testing & QA',          'testing-qa',           'Testing, QA tools, and best practices',                  'fa-vial fa-bug',                     'violet',      59),
  ('Performance',           'performance',          'Performance tuning, profiling, optimization',            'fa-gauge-high fa-chart-line',        'amber',       60),
  ('UI/UX',                 'ui-ux',                'UX research, UI patterns, and usability',                'fa-object-group fa-eye',             'purple',      61),
  ('Inspiration',           'inspiration',          'Inspiration boards, showcases, galleries',               'fa-lightbulb fa-star',               'yellow',      62),

  -- Writing / Reading
  ('Writing',               'writing',              'Writing, blogging, and publishing tools',                'fa-pen-nib fa-keyboard',             'blue-gray',   63),
  ('Books',                 'books',                'Books and reading lists',                                 'fa-book-open fa-bookmark',           'emerald',     64),
  ('Articles',              'articles',             'Long-form reads and articles',                           'fa-file-lines fa-newspaper',         'slate',       65),
  ('Blogs',                 'blogs',                'Blog posts and personal sites',                           'fa-rss fa-pen',                      'orange',      66),
  ('Newsletters',           'newsletters',          'Newsletter signups and issues',                           'fa-envelope-open-text fa-paper-plane','amber',      67),

  -- Communities
  ('Forums',                'forums',               'Forums, communities, and Q&A',                           'fa-comments fa-users',               'cyan',        68),
  ('Reddit',                'reddit',               'Reddit threads and communities',                          'fa-reddit-alien fa-comments',        'red',         69),
  ('Discord',               'discord',              'Discord servers and communities',                         'fa-discord fa-users',                'indigo',      70),
  ('Twitter/X',             'twitter-x',            'Twitter/X links and threads',                            'fa-x-twitter fa-hashtag',            'zinc',        71),

  -- Video platforms
  ('YouTube',               'youtube',              'YouTube channels and videos',                             'fa-youtube fa-play',                 'red',         72),
  ('YouTube Channels',      'youtube-channels',     'YouTube channels and creators',                           'fa-tv fa-youtube',                   'rose',        73),
  ('Shorts & Clips',        'shorts-clips',         'Short-form video clips',                                  'fa-scissors fa-video',               'orange',      74),
  ('YouTube Reactions',     'youtube-reactions',    'Reaction videos on YouTube',                              'fa-video fa-face-smile',             'dodgerblue',  75),

  -- Education
  ('Courses',               'courses',              'Online courses and structured learning',                  'fa-graduation-cap fa-book',          'green',       76),
  ('Certifications',        'certifications',       'Certification resources and prep',                        'fa-certificate fa-award',            'blue',        77),
  ('Cheat Sheets',          'cheat-sheets',         'Quick references and cheat sheets',                       'fa-note-sticky fa-bolt',             'yellow',      78),
  ('Interview Prep',        'interview-prep',       'Interview prep, questions, and practice',                'fa-user-check fa-clipboard-list',    'indigo',      79),

  -- Career
  ('Career',                'career',               'Career growth, resumes, and job resources',              'fa-briefcase fa-arrow-trend-up',     'brown',       80),
  ('Jobs',                  'jobs',                 'Job listings and job resources',                          'fa-building fa-magnifying-glass',    'slate',       81),

  -- Business / Product
  ('Startups',              'startups',             'Startup resources and founders',                          'fa-rocket fa-lightbulb',             'violet',      82),
  ('Product',               'product',              'Product management and strategy',                         'fa-cube fa-chart-line',              'teal',        83),
  ('Roadmaps',              'roadmaps',             'Roadmaps, plans, and strategy docs',                     'fa-map fa-route',                    'emerald',     84),

  -- Data
  ('Analytics',             'analytics',            'Analytics, metrics, and dashboards',                      'fa-chart-pie fa-chart-line',         'amber',       85),
  ('Data Science',          'data-science',         'Data science resources and tooling',                     'fa-chart-area fa-brain',             'cyan',        86),
  ('Datasets',              'datasets',             'Datasets and data sources',                               'fa-table fa-database',               'blue',        87),
  ('Automation',            'automation',           'Automation tools, scripts, and workflows',               'fa-gears fa-robot',                  'orange',      88),

  -- Lifestyle
  ('Home',                  'home',                 'Home-related resources and tools',                        'fa-house fa-screwdriver-wrench',     'slate',       89),
  ('Parenting',             'parenting',            'Parenting resources and guides',                          'fa-children fa-heart',               'light-pink',  90),
  ('Pets',                  'pets',                 'Pet resources and communities',                           'fa-paw fa-heart',                    'amber',       91),
  ('Cars',                  'cars',                 'Automotive news, reviews, and resources',                'fa-car fa-gauge-high',               'maroon',      92),
  ('Sports',                'sports',               'Sports resources and coverage',                           'fa-football fa-trophy',              'green',       93),
  ('Baseball',              'baseball',             'Baseball-specific content',                               'fa-baseball fa-trophy',              'light-blue',  94),
  ('Gaming',                'gaming',               'Games, gaming news, and communities',                    'fa-gamepad fa-dice',                 'purple',      95),
  ('Movies',                'movies',               'Movies and film resources',                               'fa-clapperboard fa-film',            'teal',        96),
  ('TV',                    'tv',                   'TV shows and streaming content',                          'fa-tv fa-satellite-dish',            'rose',        97),

  -- Knowledge
  ('Science',               'science',              'Science news and resources',                              'fa-atom fa-flask',                   'cyan',        98),
  ('History',               'history',              'History content and references',                          'fa-landmark fa-scroll',              'stone',       99),
  ('Politics',              'politics',             'Politics news and commentary',                            'fa-scale-balanced fa-landmark',      'red',         100),
  ('Legal',                 'legal',                'Legal resources and references',                          'fa-gavel fa-scale-balanced',         'slate',       101),

  -- Commerce / Lifestyle
  ('Real Estate',           'real-estate',          'Real estate tools and listings',                          'fa-house-chimney fa-key',            'emerald',     102),
  ('Shopping Deals',        'shopping-deals',       'Deals, coupons, and price tracking',                     'fa-tags fa-percent',                 'yellow',      103),
  ('Wishlist',              'wishlist',             'Wishlist items and purchase intent',                      'fa-heart fa-star',                   'rose',        104),

  -- Hardware / Tech
  ('Hardware',              'hardware',             'PC hardware and electronics',                             'fa-microchip fa-memory',             'blue',        105),
  ('Networking Gear',       'networking-gear',      'Routers, switches, and networking hardware',             'fa-network-wired fa-router',         'cyan',        106),

  -- Self
  ('Self Improvement',      'self-improvement',     'Habits, mindset, and self improvement',                  'fa-seedling fa-arrow-up',            'green',       107),
  ('Mindset',               'mindset',              'Mindset, motivation, and psychology',                    'fa-face-smile fa-brain',             'amber',       108),
  ('Quotes',                'quotes',               'Quotes and highlights',                                   'fa-quote-left fa-bookmark',          'slate',       109),

  -- Food specifics
  ('Recipes',               'recipes',              'Recipes and cooking resources',                           'fa-utensils fa-fire',                'amber',       110),
  ('Restaurants',           'restaurants',          'Restaurants and food spots',                              'fa-bowl-food fa-location-dot',       'orange',      111),

  -- Cannabis
  ('Cannabis',              'cannabis',             'Cannabis related bookmarks',                              'fa-cannabis fa-leaf',                'emerald',     112),
  ('Dispensaries',          'dispensaries',         'Cannabis related Dispensary bookmarks',                  'fa-cannabis fa-store',               'teal',        113),
  ('Cannabis Products',     'cannabis-products',    'Cannabis related product bookmarks',                     'fa-cannabis fa-box',                 'amber',       114),
  ('Cannabis Brands',       'cannabis-brands',      'Cannabis related brand bookmarks',                       'fa-cannabis fa-certificate',         'indigo',      115),
  ('Cannabis Connecticut',  'cannabis-connecticut', 'Cannabis related bookmarks for Connecticut',             'fa-cannabis fa-city',                'cyan',        116),
  ('Cannabis Sales',        'cannabis-sales',       'Cannabis sales related bookmarks',                       'fa-cannabis fa-tags',                'lime',        117),

  -- Politics / Geographic
  ('Democrats',             'democrats',            'Democrat related bookmarks',                              'fa-democrat fa-flag',                'royalblue',   118),
  ('New York',              'new-york',             'New York related bookmarks',                              'fa-city fa-building',                'slate',       119),
  ('Socialism',             'socialism',            'Socialism related bookmarks',                             'fa-lightbulb fa-brain',              'crimson',     120),

  -- Military
  ('Military',              'military',             'Military Related bookmarks',                              'fa-shield fa-star',                  'olive',       121),
  ('Sniper',                'sniper',               'Sniper Related bookmarks',                                'fa-person-rifle fa-crosshairs',      'gunmetal',    122),

  -- Documents
  ('Document',              'document',             'Document related bookmarks',                              'fa-file fa-folder',                  'gray',        123);
