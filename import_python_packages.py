import os
import re
import tempfile
import unicodedata
from datetime import date
from io import BytesIO
import xml.etree.ElementTree as ET

import av
import numpy as np
import pandas as pd
import requests
import matplotlib.pyplot as plt
import seaborn as sns

import streamlit as st
from streamlit_webrtc import webrtc_streamer, AudioProcessorBase

from PIL import Image
from PyPDF2 import PdfReader
from docx import Document
from dotenv import load_dotenv
from langdetect import detect
import easyocr
import fitz
from fpdf import FPDF
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

import google.generativeai as genai

from tools import update_usage
from config import BACKEND_URL

# from weasyprint import HTML