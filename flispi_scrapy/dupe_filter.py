from scrapy.dupefilters import RFPDupeFilter

class CustomDupeFilter(RFPDupeFilter):
    def request_seen(self, request):
        # Put your custom duplication filtering logic here.
        # Return True if duplicate, False otherwise.
        # If the request is to 'https://www.thelandbank.org/find_properties.asp?LRCsearch=setdo' it is not a duplicate
        if 'https://www.thelandbank.org/' in request.url:
            return False
        return super().request_seen(request)