from flask import Flask, request
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import geopandas as gpd
import networkx as nx
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from collections import Counter
from tabulate import tabulate
from flask_cors import CORS
import io
import base64
import json
import gmaps
app = Flask(__name__)




from app.views import home
