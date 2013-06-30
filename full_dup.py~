#!/usr/bin/env python


############
#Sampling Rate is common in both signal Graphs
#Subdevice spec is common in both signal Graphs
#args same
#Receiver Verbose is not set
#No asynchronous notifications to callback function at receiver

############ 

######### >> Head block terminates execution after a certain number of items been passed already, the flow graph thus does not run indefinitely.
 
 
from gnuradio import gr, eng_notation
from gnuradio import uhd
from gnuradio.eng_option import eng_option
from optparse import OptionParser
import sys

n2s = eng_notation.num_to_str

class FullDup(gr.top_block):
	def __init__(self,options,filename):
		gr.top_block.__init__(self)

		def set_usrp(self,options, sr):
			arguments="fullscale="+str(options.fullscale)	

			# Create a UHD device sink
			self.u = uhd.usrp_sink(device_addr=options.args, stream_args=uhd.stream_args('fc32', options.otw_format, args=arguments))

			# Create a UHD device source
			if options.output_shorts:
				self.v=uhd.usrp_source(device_addr=options.args, stream_args=uhd.stream_args('sc16',options.wire_format, args=options.stream_args))
				self.sink = gr.file_sink(gr.sizeof_short*2, filename)
			else:
				self.v = uhd.usrp_source(device_addr=options.args, stream_args=uhd.stream_args('fc32',
                                      options.wire_format, args=options.stream_args))
				self.sink = gr.file_sink(gr.sizeof_gr_complex, filename)
			
###########################################################################
#TRANSMIT BLOCK option parsing
			# Set the subdevice spec 
           		if (options.spec):
               			self.u.set_subdev_spec(options.spec, 0)

			# Set the gain on the usrp from options for tx
			if (options.gain_tx):
				self.u.set_gain(options.gain_tx)
			print "Actual Tx gain set to %sdB" %(eng_notation.num_to_str(self.u.get_gain()),)

			# Set the antenna 
			if (options.antenna):
				self.u.set_antenna(options.antenna_tx, 0)

			# Set freq
			target_freq_tx = options.freq_tx
			tr = self.u.set_center_freq(target_freq_tx)
			if tr is not None:
				print "Set center frequency to %sHz" %(eng_notation.num_to_str(self.u.get_center_freq()),)
                		print "Tx RF frequency:  %sHz" %(eng_notation.num_to_str(tr.actual_rf_freq),)
                		print "Tx DSP frequency: %sHz" %(eng_notation.num_to_str(tr.actual_dsp_freq),)
			else:
				print "Failed to set Frequency"


			# Set sampling rate
            		self.u.set_samp_rate(sr)
           		sra = self.u.get_samp_rate()
            		print ""
            		print "Actual sampling rate set to %sSps" %(eng_notation.num_to_str(sra),)
           		print "Actual chip rate set to %sCps" %(eng_notation.num_to_str(sra/sps),)



		# Generate m-sequence
       		degree = int(options.degree)
       		self.period = 2**degree - 1
        	self.lfsr = gr.glfsr_source_b(degree, True)

		# Map to constellation
        	self.constellation = [-1, 1]
        	self.mapper = gr.chunks_to_symbols_bf(self.constellation)


		sps = 2
       		self.excess_bw = options.excess_bw
        	# Set target sampling rate to 2*chip rate
        	samp_rate = sps*options.chip_rate



		# Create RRC with specified excess bandwidth
        	self.taps = gr.firdes.root_raised_cosine(1.0,sps,1.0,self.excess_bw,11*sps)
		self.rrc = gr.interp_fir_filter_fff(sps,self.taps) 


		set_usrp(self,options,samp_rate)


		setup_usrp(self,options,samp_rate)

		self.convert = gr.float_to_complex(1)
		self.connect(self.lfsr, self.mapper, self.rrc, self.convert, self.u)

###########################################################################


###########################################################################
#RECEIVER BLOCK option parsing
		# Set the subdevice spec
       		if(options.spec):
       			self.v.set_subdev_spec(options.spec, 0)

		# Set the antenna
		if(options.antenna):
			self.v.set_antenna(options.antenna_rx, 0)
			
		# Set receiver sample rate
       		self.v.set_samp_rate(options.samp_rate)

		# Set receive daughterboard gain
		if options.gain is None:
			g = self.v.get_gain_range()
			options.gain = float(g.start()+g.stop())/2
			print "Using mid-point gain of", options.gain, "(", g.start(), "-", g.stop(), ")"
		self._u.set_gain(options.gain)

		# Set frequency (tune request takes lo_offset)		
		if(options.lo_offset is not None):
       			treq = uhd.tune_request(options.freq_rx, options.lo_offset)
		else:
			treq = uhd.tune_request(options.freq_rx)
		tr = self.v.set_center_freq(treq)
		if tr==None:
			sys.stderr.write('Failed to set Receiver Center Frequency\n')
       			raise SystemExit, 1


		# Create head block if needed and wire it up
		if options.nsamples_rx is None:
       			self.connect(self.v, self.sink)
		else:
			if options.output_shorts:
				self.head_rx = gr.head(gr.sizeof_short*2, int(options.nsamples_rx))
			else:
				self.head_rx= gr.head(gr.sizeof_gr_complex, int(options.nsamples_rx))
			self.connect(self.v, self.head, self.sink)

		input_rate = self.v.get_samp_rate()

###########################################################################


def get_options():
	usage="%prog: [options]"
	parser = OptionParser(option_class=eng_option, usage=usage)
	#parser.add_option("-S", "--save", type="string", default=None, help="Save pulse shape, m-seq, and other info to file SAVE.m")
	parser.add_option("-c", "--chip-rate", type="eng_float", default=1e6,help="set chip rate [default=%default]")
	parser.add_option("-d", "--degree", type="eng_float", default=7,help="degree of LFSR, [default=%default]")
	parser.add_option("-x", "--excess-bw", type="eng_float", default=0.5,help="set excess BW/ roll-off factor, [default=%default]")
	parser.add_option("-a", "--args", type="string", default="",help="UHD device address args , [default=%default]")
	#parser.add_option("-a", "--args_tx", type="string", default="",help="UHD device address args , [default=%default]")
	parser.add_option("", "--spec", type="string", default=None,help="Subdevice of UHD device where appropriate")
	parser.add_option("", "--antenna", type="string", default=None,help="select Tx Antenna where appropriate")
	parser.add_option("", "--freq_rx", type="eng_float", default=None,help="set frequency to FREQ", metavar="FREQ")
	parser.add_option("", "--freq_tx", type="eng_float", default=None,help="set frequency to FREQ", metavar="FREQ")
	parser.add_option("-g", "--gain", type="eng_float", default=0.0,help="set gain in dB, [default=%default]")
	parser.add_option("", "--otw-format", type="string", default="sc16",help="set over-the-wire format to USRP [default=%default]")
	parser.add_option("", "--fullscale", type="eng_float", default=1.0,help="set full scale value for complex32 format [default=%default]")	
	(options, args) = parser.parse_args ()
	if len(args)!=1:
		parser.print_help()
		raise SystemExit, 1

	if options.freq_rx is None:
		parser.print_help()
        	sys.stderr.write('You must specify the Receiver frequency with -f_rx FREQ\n');
        	raise SystemExit, 1
	
	if options.freq_tx is None:
		parser.print_help()
        	sys.stderr.write('You must specify the Transmit frequency with -f_tx FREQ\n');
        	raise SystemExit, 1	

	return options	

if __name__=='__main__':
	(options, filename)=get_options()
	tb=FullDup(options,filename)

	try:
		tb.run()
	except KeyboardInterrupt:
		pass

