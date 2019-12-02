import re
import scrapy

from urllib.parse import urljoin


class ImfSpider(scrapy.Spider):
    name = 'imf'
    allowed_domains = ['imf.org']
    start_urls = ['https://www.imf.org/en/Publications/Search'
                  '?series=IMF Staff Country Reports']

    def parse(self, response):
        # iterate over publications
        for pub in response.css('.pub-row>h6>a'):
            yield response.follow(pub, self.parse_pub)

        # iterate over follow-up pages
        for page in response.css('.pages a'):
            yield response.follow(page, self.parse)

    def parse_pub(self, response):
        # selectors
        content = response.css('article .content')
        download = content.css('.piwik_download')
        sections = content.css('section')
        title = content.css('h2')

        # item title
        title = title.css('::text').get()

        # item files
        links = download.css('::attr(href)').getall()
        files = [urljoin(response.url, link) for link in links]

        # item metas/langs
        metas = dict()
        languages = dict()
        for section in sections:
            language = section.css('h5::text').get()
            labels = section.css('.pub-label')
            descs = section.css('.pub-desc')

            if language is not None:
                languages[language] = dict()

            assert len(labels) == len(descs)

            for label, desc in zip(labels, descs):
                desc_text = '\n'.join(desc.css('::text').getall())
                desc_text = re.sub(r'\s+', ' ', desc_text.strip())
                label_text = '\n'.join(label.css('::text').getall())

                if language is None:
                    metas[label_text] = desc_text
                else:
                    languages[language][label_text] = desc_text

        yield {
            'metas': metas,
            'title': title,
            'file_urls': files,
            'languages': languages,
        }
