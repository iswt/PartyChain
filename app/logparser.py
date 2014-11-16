import re

def formatted(f):
	return format(f, ',.8f').rstrip('0').rstrip('.')

class CounterpartydLogParser():
	
	timestamp_regex = r'(\d\d\d\d-\d\d-\d\d-.\d\d:\d\d:\d\d.\d\d\d\d)'
	cmnd_regex = r'(.+?): '
	block_regex = r'([\d]+)'
	send_regex = r'([\d\.]*) (.+) from (.+) to (.+) \((.+)\) \[(.+)\]'
	
	bet_regex = r'([\d\.]*) (.+) against ([\d\.]*) (.+), by (.+), on (.+) that (.+) will (.+) ([\d\.]*) at (\d\d\d\d-\d\d-\d\d.\d\d:\d\d:\d\d.\d\d:\d\d), in (.+) blocks \((.+)\) \[(.+)\]'
	expired_bet_regex = r'(.+)'
	
	rps_regex = r'(.+) opens game with (\d+) possible moves and a wager of ([\d\.]*) (.+)'
	rps_match_regex = r'(.+) is playing a (\d+)-moves game with (.+) with a wager of ([\d\.]*) (.+) \((.+)\) \[(.+)\]'
	rps_resolved_regex1 = r'([a-zA-Z0-9]+) \[(.+)\]'
	rps_resolved_regex2 = r'(.+) is playing (\d+) on a (\d+)-moves game with (.+) with a wager of ([\d\.]*) (.+) \((.+)\) \[(.+)\]'
	rps_expired_regex = r'(.+)'
	
	def __init__(self):
		pass
	
	def parse(self, line):
		retd = {}
		
		s = re.search(
			self.timestamp_regex + self.cmnd_regex,
			line
		)
		timestamp = s.group(1)
		cmnd = s.group(2).strip(' ')
		
		retd['timestamp'] = timestamp
		retd['command'] = cmnd
		
		if cmnd == 'Send':
			self.parseSend(line, retd)
		elif cmnd == 'Issuance':
			self.parseIssuance(line, retd)
		elif cmnd == 'Block':
			self.parseBlock(line, retd)
		#*Bet**************************************
		elif cmnd == 'Bet':
			self.parseBet(line, retd)
		elif cmnd == 'Expired bet':
			self.parseExpiredBet(line, retd)
		#*******************************************
		elif cmnd == 'Order':
			pass
		#*RPS **************************************
		elif cmnd == 'RPS':
			self.parseRPS(line, retd)
		elif cmnd == 'RPS Match':
			self.parseRPSMatch(line, retd)
		elif cmnd == 'RPS Resolved':
			self.parseRPSResolved(line, retd)
		elif cmnd == 'Expired RPS' or cmnd == 'Expired RPS Match':
			self.parseRPSExpired(line, retd)
		#*********************************************
		else:
			pass
		
		return retd
	
	def parseSend(self, line, d):
		s = re.search(
			self.timestamp_regex + self.cmnd_regex + self.send_regex,
			line
		)
		d['amount'] = formatted(float(s.group(3)))
		
		d['asset'] = s.group(4)
		d['fromaddress'] = s.group(5)
		d['toaddress'] = s.group(6)
		d['tx_hash'] = s.group(7)
		d['validity'] = s.group(8)
	
	def parseIssuance(self, line, d):
		s = line.split(' ')
		d['actionaddress'] = s[2]
		d['issueaction'] = s[3]
		
		if d['issueaction'] == 'created':
			validity = s[-1].replace('[', '')
			validity = validity.replace(']', '')
			txhash = s[-2].replace('(', '')
			txhash = txhash.replace(')', '')
			
			d['validity'] = validity
			d['tx_hash'] = txhash
			
			d['issue_amount'] = formatted(float(s[4]))
			
			d['issue_asset'] = s[7][:-1]
			d['divisibility'] = s[10]
			d['callability'] = s[12]
			if s[13] == 'with': # description
				d['callability'] = s[12][:-1]
				d['description'] = ''
				for desc in s[15 : -2]:
					d['description'] += '{0} '.format(desc)
			elif s[13] == 'from':
				'''original_asset_issuedate = s[14]
				original_asset_issueamnt = s[16]
				original_asset_currencypair = s[17]'''
				d['original_asset_issuedate'] = s[14]
				d['original_asset_issueamnt'] = s[16]
				d['original_asset_currencypair'] = s[17]
				
				d['description'] = ''
				for desc in s[20 : -2]:
					d['description'] += '{0} '.format(desc)
			
		elif d['issueaction'] == 'locked':
			validity = s[-1].replace('[', '')
			validity = validity.replace(']', '')
			txhash = s[-2].replace('(', '')
			txhash = txhash.replace(')', '')
			
			d['validity'] = validity
			d['tx_hash'] = txhash
			
			d['locked_asset'] = s[5]
			
		else:
			pass
	
	def parseBlock(self, line, d):
		s = re.search(
			self.timestamp_regex + self.cmnd_regex + self.block_regex,
			line
		)
		d['blockheight'] = s.group(3)
	
	def parseBet(self, line, d):
		s = re.search(
			self.timestamp_regex + self.cmnd_regex + self.bet_regex,
			line
		)
		d['bet_amount'] = formatted(float(s.group(3)))
		d['bet_asset'] = s.group(4)
		d['against_amount'] = formatted(float(s.group(5)))
		d['against_asset'] = s.group(6)
		d['better_address'] = s.group(7)
		d['on_address'] = s.group(8)
		d['feed'] = s.group(9)
		d['feed_url'] = s.group(9).decode('unicode_escape').encode('ascii', 'ignore')
		d['operator'] = s.group(10)
		d['operator_amount'] = formatted(float(s.group(11)))
		d['bet_timestamp'] = s.group(12)
		d['in_blocks'] = s.group(13)
		d['tx_hash'] = s.group(14)
		d['validity'] = s.group(15)
	
	def parseExpiredBet(self, line, d):
		s = re.search(
			self.timestamp_regex + self.cmnd_regex + self.expired_bet_regex,
			line
		)
		d['tx_hash'] = s.group(3)
	
	def parseRPS(self, line, d):
		s = re.search(
			self.timestamp_regex + self.cmnd_regex + self.rps_regex,
			line
		)
		d['starter_address'] = s.group(3)
		d['possible_moves'] = s.group(4)
		d['wager_amount'] = formatted(float(s.group(5)))
		d['wager_asset'] = s.group(6)
	
	def parseRPSMatch(self, line, d):
		s = re.search(
			self.timestamp_regex + self.cmnd_regex + self.rps_match_regex,
			line
		)
		d['counterparty_address'] = s.group(3)
		d['possible_moves'] = s.group(4)
		d['starter_address'] = s.group(5)
		d['wager_amount'] = formatted(float(s.group(6)))
		d['wager_asset'] = s.group(7)
		d['tx_hash'] = s.group(8)
		d['state'] = s.group(9)
	
	def parseRPSResolved(self, line, d):
		s = re.search(
			self.timestamp_regex + self.cmnd_regex + self.rps_resolved_regex1,
			line
		)
		if not s:
			s = re.search(
				self.timestamp_regex + self.cmnd_regex + self.rps_resolved_regex2,
				line
			)
			d['counterparty_address'] = s.group(3)
			d['counterparty_move'] = s.group(4)
			d['possible_moves'] = s.group(5)
			d['starter_address'] = s.group(6)
			d['wager_amount'] = formatted(float(s.group(7)))
			d['wager_asset'] = s.group(8)
			d['tx_hash'] = s.group(9)
			d['state'] = s.group(10)
		else:
			d['tx_hash'] = s.group(3)
			d['state'] = s.group(4)
		
	def parseRPSExpired(self, line, d):
		s = re.search(
			self.timestamp_regex + self.cmnd_regex + self.rps_expired_regex,
			line
		)
		d['tx_hash'] = s.group(3)
	