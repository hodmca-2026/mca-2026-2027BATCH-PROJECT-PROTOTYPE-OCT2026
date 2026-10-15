import scrapy

class FoodProductItem(scrapy.Item):
    url = scrapy.Field()
    page_title = scrapy.Field()
    product_name = scrapy.Field()
    brand = scrapy.Field()
    category = scrapy.Field()
    ingredients = scrapy.Field()
    claims = scrapy.Field()
    calories = scrapy.Field()
    sugar = scrapy.Field()
    total_fat = scrapy.Field()
    saturated_fat = scrapy.Field()
    protein = scrapy.Field()
    fibre = scrapy.Field()
    salt = scrapy.Field()
    image_url = scrapy.Field()
    source = scrapy.Field()
