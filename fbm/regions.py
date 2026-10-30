"""
fbm/regions.py — US states + territories, sales-tax profile, facilitator rules.
"""
from __future__ import annotations

NO_STATE_TAX = {"NH", "OR", "MT", "DE", "AK"}
TERRITORIES = {"PR", "GU", "VI", "AS", "MP"}

STATES = {
 "AL":("Alabama",4.0),"AK":("Alaska",0.0),"AZ":("Arizona",5.6),"AR":("Arkansas",6.5),
 "CA":("California",7.25),"CO":("Colorado",2.9),"CT":("Connecticut",6.35),"DE":("Delaware",0.0),
 "DC":("District of Columbia",6.0),"FL":("Florida",6.0),"GA":("Georgia",4.0),"HI":("Hawaii",4.0),
 "ID":("Idaho",6.0),"IL":("Illinois",6.25),"IN":("Indiana",7.0),"IA":("Iowa",6.0),
 "KS":("Kansas",6.5),"KY":("Kentucky",6.0),"LA":("Louisiana",4.45),"ME":("Maine",5.5),
 "MD":("Maryland",6.0),"MA":("Massachusetts",6.25),"MI":("Michigan",6.0),"MN":("Minnesota",6.875),
 "MS":("Mississippi",7.0),"MO":("Missouri",4.225),"MT":("Montana",0.0),"NE":("Nebraska",5.5),
 "NV":("Nevada",6.85),"NH":("New Hampshire",0.0),"NJ":("New Jersey",6.625),"NM":("New Mexico",4.875),
 "NY":("New York",4.0),"NC":("North Carolina",4.75),"ND":("North Dakota",5.0),"OH":("Ohio",5.75),
 "OK":("Oklahoma",4.5),"OR":("Oregon",0.0),"PA":("Pennsylvania",6.0),"RI":("Rhode Island",7.0),
 "SC":("South Carolina",6.0),"SD":("South Dakota",4.2),"TN":("Tennessee",7.0),"TX":("Texas",6.25),
 "UT":("Utah",6.1),"VT":("Vermont",6.0),"VA":("Virginia",5.3),"WA":("Washington",6.5),
 "WV":("West Virginia",6.0),"WI":("Wisconsin",5.0),"WY":("Wyoming",4.0),
 "PR":("Puerto Rico",10.5),"GU":("Guam",4.0),"VI":("US Virgin Islands",5.0),
 "AS":("American Samoa",0.0),"MP":("Northern Mariana Islands",5.0),
}

LOW_1099K = {"AR":2500,"IL":1000,"MA":600,"MD":600,"NJ":1000,"VA":600,"VT":600,
             "DC":600,"MO":1200,"NC":20000}


def profile(code):
    code = (code or "TN").upper()
    if code not in STATES:
        raise ValueError(f"unknown state/territory: {code}")
    name, rate = STATES[code]
    has_tax = code not in NO_STATE_TAX
    return {
        "code": code, "name": name, "base_rate": rate,
        "has_sales_tax": has_tax,
        "marketplace_facilitator": has_tax,
        "facilitator_threshold": 100000,
        "k1099_threshold": LOW_1099K.get(code, 20000),
        "is_territory": code in TERRITORIES,
        "business_registration": "Dept of Revenue business tax registration" if has_tax else "none",
    }


def list_all():
    return [{"code": c, "name": STATES[c][0], "territory": c in TERRITORIES}
            for c in sorted(STATES)]