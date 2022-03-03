#!/usr/bin/env python3

import argparse
import asyncio
import concurrent.futures
import http.server
import json
import logging
import multiprocessing
import os
import socketserver
import time

import kociemba
import websockets


KOCIEMBA_MAX_DEPTH = 20


logger = logging.getLogger("Rubik's Cube Solver")


def time_kociemba_solve(*args, **kwargs):
	t = time.time()
	solution = kociemba.solve(*args, **kwargs)
	return {'time': time.time() - t, 'solution': solution}


async def websocket_echo(websocket, executor):
	async for scramble in websocket:
		logger.info(f'Received scramble: {scramble}')

		try:
			f = executor.submit(time_kociemba_solve, scramble, max_depth=KOCIEMBA_MAX_DEPTH)
			await asyncio.wrap_future(f)
			data = f.result()
		except ValueError:
			logger.info(f'Invalid scramble: {scramble}')
			await websocket.send('invalid')
		else:
			logger.info(f'Scramble "{scramble}" solved: {data["solution"]} ({data["time"]}s)')
			await websocket.send(json.dumps(data))


async def websocket_server(fn, host='0.0.0.0', port=8080, max_workers=1):
	with concurrent.futures.ProcessPoolExecutor(max_workers) as executor:
		async with websockets.serve(lambda websocket: fn(websocket, executor), host, port):
			await asyncio.Future()


def main():
	parser = argparse.ArgumentParser(description="Rubik's Cube Solver Webserver")
	parser.add_argument('--directory', default='./rubiks-cube-gui/dist', help='Webserver root directory')
	parser.add_argument('--host', default='0.0.0.0', help='Webserver host')
	parser.add_argument('--port', type=int, default=80, help='Webserver port')
	parser.add_argument('--ws-host', default='0.0.0.0', help='Websocket server host')
	parser.add_argument('--ws-port', type=int, default=8080, help='Websocket server port')
	parser.add_argument('--max-depth', type=int, default=20, help='Kociemba algorithm max depth')
	parser.add_argument('--max-workers', type=int, default=1, help='Maximum number of workers for parallel solves')

	args = parser.parse_args()

	global KOCIEMBA_MAX_DEPTH
	KOCIEMBA_MAX_DEPTH = args.max_depth

	os.chdir(args.directory)

	logger.addHandler(logging.StreamHandler())
	logger.setLevel(logging.INFO)

	websocket_server_process = multiprocessing.Process(
		name='Websocket server',
		target=lambda *args: asyncio.run(websocket_server(*args)),
		args=(websocket_echo, args.ws_host, args.ws_port, args.max_workers),
	)
	logger.info(f'Starting websocket server at {args.ws_host}:{args.ws_port}!')
	websocket_server_process.start()

	logger.info(f'Starting webserver at {args.host}:{args.port}!')

	server = socketserver.TCPServer((args.host, args.port), http.server.SimpleHTTPRequestHandler)

	try:
		server.serve_forever()
	except KeyboardInterrupt:
		logger.info('Exiting websocket server')
		websocket_server_process.kill()
		logger.info('Exiting webserver')
		websocket_server_process.join()


if __name__ == '__main__':
	main()
