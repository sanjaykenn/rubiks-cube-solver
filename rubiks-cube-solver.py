import argparse
import http.server
import json
import logging
import os
import socketserver
import time
import urllib.parse

import kociemba


logger = logging.getLogger("Rubik's Cube Solver")


class RubiksCubeHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
	def do_GET(self):
		if self.path.startswith('/solve'):
			query = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)

			if 'scramble' not in query:
				self.send_error(400)
				return

			data = {}

			try:
				logger.info(f'Solving scramble {query["scramble"][0]}')
				t = time.time()
				data['solution'] = kociemba.solve(query['scramble'][0])
				data['time'] = time.time() - t
				logger.info(f'Solved scramble {query["scramble"][0]}: {data["solution"]}')
			except ValueError:
				logger.error(f'Invalid scramble {query["scramble"][0]}')
				self.send_error(400)
				return

			self.send_response(200)
			self.send_header('Content-type', 'application/json')
			self.end_headers()
			self.wfile.write(json.dumps(data).encode())
		else:
			return http.server.SimpleHTTPRequestHandler.do_GET(self)


if __name__ == '__main__':
	parser = argparse.ArgumentParser(description="Rubik's Cube Solver Webserver")
	parser.add_argument('--directory', default='./rubiks-cube-gui/dist', help='Webserver root directory')
	parser.add_argument('--host', default='0.0.0.0', help='Webserver host')
	parser.add_argument('--port', type=int, default=80, help='Webserver port')

	args = parser.parse_args()

	os.chdir(args.directory)

	logger.addHandler(logging.StreamHandler())
	logger.setLevel(logging.INFO)

	logger.info(f'Starting server at {args.host}:{args.port}!')

	server = socketserver.TCPServer((args.host, args.port), RubiksCubeHTTPRequestHandler)
	server.serve_forever()
