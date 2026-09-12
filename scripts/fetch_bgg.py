#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
fetch_bgg.py - Download a BoardGameGeek dataset via the offical XML API2.

Why this script exists
----------------------
Since fall 2025 BGG requires a Bearer token (register your app at
https://boardgamegeek.com/applications, then generate a token).

This script:
    1. GET
    2. GET
    3. GET
and finally saves all games into a single games.csv file.

Rate limiting: BGG limits the XML API to ~100 requests/min. This script stays
well below that (3.5s between requests) and backs off on HTTP 429 / 5xx.
Raw responses are cached in <out>/raw/ so re-runs do not re-download.

Usage
-----
    export BGG_API_TOKEN="your token"
    python3 fetch_bgg.py [--out data] [--sleep 3.5]

Requires only the Python standard library (urlib + xml.etree)
"""

import argparse
import csv
import html
import os
import pathlib
import re
import sys
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

BASE = "https://boardgamegeek.com/xmlapi2"
UA = "DS-DataScienceProject/1.0 (student mini-project)"

DEFAULT_SERACH_TERMS = [
    # strategy / euro
    "Catan", "Carcassonne", "Ticket to Ride", "Pandemic", "Gloomhaven",
    "Terraformng Mars", "Wingspan", "Azul", "Splendor", "7 Wonders",
    "Dominion", "Agricola", "Puerto Rico", "Power Grid", "Scythe", "Root",
    "Everdell", "Spirit Island", "Brass", "Great Western Trail",
    "Castles of Burgundy", "Viticulture", "Ark Nova", "Dune Imperium",
    "Twilight Imperium", "War of the Ring", "Gaia Project", 
    "A Feast for Odin", "El Grande", "Food Chain Magnate",
    # abstract / family / party
    "Chess", "Go", "Hive", "Patchwork", "Santorini", "Qwirkle",
    "Just one", "Wavelength", "Codenames", "Dixit", "Hanabi",
    "Monopoly", "Uno", "Exploding Kittens", "Scrabble", "Risk", "Jenga",
    # thematic / cooperative
    "Mysterium", "Marvel Champions", "Arkham Horror", "Descent",
    "Mansions of Madness", "Nemesis", "Dead of Winter",
]

def log(msg: str) -> None:
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


def