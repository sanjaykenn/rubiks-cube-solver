import argparse
import http.server
import os
import socketserver


class RubiksCubeHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
	def do_GET(self):
		if self.path.startswith('/solve'):
			self.send_response(200)
			self.send_header('Content-type', 'text/plain')
			self.end_headers()
			self.wfile.write(b"R U R' U'")
		else:
			return http.server.SimpleHTTPRequestHandler.do_GET(self)


if __name__ == '__main__':
	parser = argparse.ArgumentParser(description="Rubik's Cube Solver Webserver")
	parser.add_argument('--directory', default='./rubiks-cube-gui/dist', help='Webserver root directory')
	parser.add_argument('--host', default='0.0.0.0', help='Webserver host')
	parser.add_argument('--port', type=int, default=80, help='Webserver port')

	args = parser.parse_args()

	os.chdir(args.directory)

	server = socketserver.TCPServer((args.host, args.port), RubiksCubeHTTPRequestHandler)
	server.serve_forever()
