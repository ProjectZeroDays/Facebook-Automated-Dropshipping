import sys
from fbm import core, bot, scraper, watcher, inbox, crosslist, crosslist_post, \
                copygen, validate, targets, reprice, groups, returns, tax, \
                accounts, suppliers, tracking, samples, session_guard, insights
for old, mod in {"fbm_core": core, "fb_marketplace_bot": bot, "competitor_scraper": scraper,
                 "sale_watcher": watcher, "inbox_poller": inbox, "copy_generator": copygen,
                 "fbm_validate": validate, "targets_builder": targets}.items():
    sys.modules.setdefault(old, mod)
