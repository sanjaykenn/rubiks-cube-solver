#!/usr/bin/env python

import argparse
import asyncio
import http.server
import json
import logging
import os
import socketserver
import threading
import time

import kociemba
import websockets


KOCIEMBA_MAX_DEPTH = 20


logger = logging.getLogger("Rubik's Cube Solver")


async def websocket_echo(websocket):
	async for scramble in websocket:
		logger.info(f'Received scramble: {scramble}')

		t = time.time()
		try:
			solution = kociemba.solve(scramble, max_depth=KOCIEMBA_MAX_DEPTH)
		except ValueError:
			logger.info(f'Invalid scramble: {scramble}')
			await websocket.send('invalid')
		else:
			data = {'time': time.time() - t, 'solution': solution}
			logger.info(f'Scramble "{scramble}" solved: {solution} ({data["time"]}s)')
			await websocket.send(json.dumps(data))


async def websocket_server(fn, host='0.0.0.0', port=8080):
	async with websockets.serve(fn, host, port):
		await asyncio.Future()


def main():
	parser = argparse.ArgumentParser(description="Rubik's Cube Solver Webserver")
	parser.add_argument('--directory', default='./rubiks-cube-gui/dist', help='Webserver root directory')
	parser.add_argument('--host', default='0.0.0.0', help='Webserver host')
	parser.add_argument('--port', type=int, default=80, help='Webserver port')
	parser.add_argument('--ws-host', default='0.0.0.0', help='Websocket server host')
	parser.add_argument('--ws-port', type=int, default=8080, help='Websocket server port')
	parser.add_argument('--max-depth', type=int, default=8080, help='Kociemba algorithm max depth')

	args = parser.parse_args()

	global KOCIEMBA_MAX_DEPTH
	KOCIEMBA_MAX_DEPTH = args.max_depth

	os.chdir(args.directory)

	logger.addHandler(logging.StreamHandler())
	logger.setLevel(logging.INFO)

	logger.info(f'Starting websocket server at {args.ws_host}:{args.ws_port}')
	threading.Thread(
		target=asyncio.run,
		args=(websocket_server(websocket_echo, args.ws_host, args.ws_port),)
	).start()

	logger.info(f'Starting webserver at {args.host}:{args.port}!')

	server = socketserver.TCPServer((args.host, args.port), http.server.SimpleHTTPRequestHandler)
	server.serve_forever()


if __name__ == '__main__':
	main()
