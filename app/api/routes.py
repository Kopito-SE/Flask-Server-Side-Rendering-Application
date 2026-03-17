from flask import Blueprint, jsonify, request
from flask_restful import Api, Resource
from ..models import Product, Category, User, Order, OrderItem

api_bp = Blueprint("api", __name__, url_prefix="/api")
api = Api(api_bp)