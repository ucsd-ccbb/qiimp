import os

import tornado.ioloop
import tornado.web


class MainHandler(tornado.web.RequestHandler):

    def get(self):
        self.render("test_json_editor_template.html")

    def post(self):
        noun1 = self.get_argument('schema_json')
        self.write(noun1)

if __name__ == "__main__":
    settings = {
        "static_path": os.path.dirname(__file__)
    }
    application = tornado.web.Application([
        (r"/", MainHandler),
        (r"/(apple-touch-icon\.png)", tornado.web.StaticFileHandler,
         dict(path=settings['static_path'])),
    ], **settings)

    application.listen(8898)
    tornado.ioloop.IOLoop.instance().start()
