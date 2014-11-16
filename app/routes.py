from flask import Flask, render_template, url_for
from flask import request, session, redirect
from flask import copy_current_request_context

from flask.ext.socketio import SocketIO, emit

from app import app
from app import socketio

import pytz
import time
import datetime

import json
import re

import tailer
from threading import Thread

from logparser import CounterpartydLogParser
cpl = CounterpartydLogParser()

numtorps = {
	1: 'rock',
	2: 'paper',
	3: 'scissors',
	4: 'lizard',
	5: 'spock'
}

tailer_file = '/home/xcp/.config/counterpartyd/counterpartyd.log'

@socketio.on('new connection', namespace='/counterpartywatch')
def connection_func_socket(data):
	pass

def watch_thread(data):
	for l in tailer.follow(open(tailer_file)):
		try:
			d = cpl.parse(l)
		except Exception, e:
			continue
		
		actiontime = datetime.datetime.strptime(d['timestamp'], '%Y-%m-%d-T%H:%M:%S+0000')
		currenttime = datetime.datetime.utcnow()
		diff = currenttime - actiontime
		# strip microseconds
		currenttime = currenttime.strftime("%Y-%m-%d %H:%M:%S")
		
		d['timestamp_utc'] = str(actiontime)
		d['timestamp_tz'] = datetime.datetime.now(pytz.timezone('America/Denver')).strftime('%Y-%m-%d %H:%M:%S') # <-- this does not 
		d['current_timestamp'] = str(currenttime)
		d['timestamp_diff'] = str(diff)
		
		socketio.emit('new actiontime', d, namespace='/counterpartywatch')
		
		if d['command'] == 'Send':
			socketio.emit('new send', d, namespace='/counterpartywatch')
			
		elif d['command'] == 'Issuance':
			if d['issueaction'] == 'created':
				socketio.emit('new issuance', d, namespace='/counterpartywatch')
			elif d['issueaction'] == 'locked':
				socketio.emit('new lock', d, namespace='/counterpartywatch')
				
		#*RPS************************************************
		elif d['command'] == 'RPS':
			socketio.emit('new rps', d, namespace='/counterpartywatch')
			
		elif d['command'] == 'RPS Match':
			d['tx_hash'] = d['tx_hash'][0 : 64] # truncate tx_hash to first 64 characters
			socketio.emit('rps match', d, namespace='/counterpartywatch')
			
		elif d['command'] == 'RPS Resolved':
			d['tx_hash'] = d['tx_hash'][0 : 64] # truncate tx_hash to first 64 characters
			if 'counterparty_move' in d.keys():
				d['counterparty_move_text'] = numtorps[int(d['counterparty_move'])]
			
			socketio.emit('rps resolved', d, namespace='/counterpartywatch')
			
		elif d['command'] == 'Expired RPS':
			d['tx_hash'] = d['tx_hash'][0 : 64] # truncate tx_hash to first 64 characters
			socketio.emit('rps expired', d, namespace='/counterpartywatch')
			
		elif d['command'] == 'Expired RPS Match':
			d['tx_hash'] = d['tx_hash'][0 : 64]
			socketio.emit('rps expiredmatch', d, namespace='/counterpartywatch')
		#******************************************************
		elif d['command'] == 'Bet':
			socketio.emit('new bet', d, namespace='/counterpartywatch')
		elif d['command'] == 'Expired bet':
			socketio.emit('expired bet', d)
		elif d['command'] == 'Block':
			socketio.emit('new block', d, namespace='/counterpartywatch')
		

thr = Thread(target = watch_thread, args=['connected'])
thr.start()

@app.route('/', methods=['GET'])
def home():
	return render_template('home.html')
