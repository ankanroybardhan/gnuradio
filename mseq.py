#!/usr/bin/env python
 
 
 
from gnuradio import gr, eng_notation
from gnuradio import uhd
from gnuradio.eng_option import eng_option
from optparse import OptionParser
import sys
 
class tx_mseq_block(gr.top_block):
 
    def __init__(self, options):
        gr.top_block.__init__(self)
 
        def setup_usrpx(self, options, sr):
            arguments="fullscale="+str(options.fullscale)
            # Create a UHD device source
            self.u = uhd.usrp_sink(device_addr=options.args, stream_args=uhd.stream_args('fc32', options.otw_format, args=arguments))
 
 
            # Set the subdevice spec
            if (options.spec):
                self.u.set_subdev_spec(options.spec, 0)
 
            # Set the gain on the usrp from options
            if (options.gain):
                self.u.set_gain(options.gain)
            print "Actual Tx gain set to %sdB" %(eng_notation.num_to_str(self.u.get_gain()),)
 
            # Set the antenna
            if (options.antenna):
                self.u.set_antenna(options.antenna, 0)  
 
            # Set freq
            target_freq = options.freq_rx
            tr = self.u.set_center_freq(target_freq)
            if tr is not None:
                print "Set center frequency to %sHz" %(eng_notation.num_to_str(self.u.get_center_freq()),)
                print "Tx RF frequency:  %sHz" %(eng_notation.num_to_str(tr.actual_rf_freq),)
                print "Tx DSP frequency: %sHz" %(eng_notation.num_to_str(tr.actual_dsp_freq),)
            else:
                print "Failed to set freq." 
 
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
        self.taps = gr.firdes.root_raised_cosine(1.0,       # Gain
                                            sps,            # Samples per symbol
                                            1.0,            # Symbol rate
                                            self.excess_bw, # Roll-off factor
                                            11*sps)         # Number of taps
 
 
 
        self.rrc = gr.interp_fir_filter_fff(sps,            # Interpolation rate
                                             self.taps)     # FIR taps
 
 
        setup_usrpx(self, options, samp_rate)
 
        if options.save is not None:
            self.f1 = open(str(options.save)+'.m', 'w')
            sra = self.u.get_samp_rate()
            print>>self.f1, 'fc= %s;' %(self.u.get_center_freq(),)
            print>>self.f1, 'fs= %s;' %(sra,)
            print>>self.f1, 'fchip= %s;' %(sra/sps,)
            print>>self.f1, 'excess_bw= %s;' %(self.excess_bw,)
            print>>self.f1, 'ps=[' + str(self.taps).strip('()') + '];' 
            self.head = gr.head(gr.sizeof_float, self.period)
            self.sink = gr.vector_sink_f(1)
            self.connect(self.lfsr, self.mapper, self.head, self.sink)
        else:
            self.convert = gr.float_to_complex(1)
            self.connect(self.lfsr, self.mapper, self.rrc, self.convert, self.u)
 
 
 
 
def get_options():
    usage="%prog: [options]"
    parser = OptionParser(option_class=eng_option, usage=usage)
    parser.add_option("-S", "--save", type="string", default=None,
                      help="Save pulse shape, m-seq, and other info to file SAVE.m")
    parser.add_option("-c", "--chip-rate", type="eng_float", default=1e6,
                      help="set chip rate [default=%default]")
    parser.add_option("-d", "--degree", type="eng_float", default=7,
                      help="degree of LFSR, [default=%default]")
    parser.add_option("-x", "--excess-bw", type="eng_float", default=0.5,
                      help="set excess BW/ roll-off factor, [default=%default]")
    parser.add_option("-a", "--args", type="string", default="",
                      help="UHD device address args , [default=%default]")
    parser.add_option("", "--spec", type="string", default=None,
                      help="Subdevice of UHD device where appropriate")
    parser.add_option("", "--antenna", type="string", default=None,
                      help="select Tx Antenna where appropriate")
    parser.add_option("-f", "--freq_rx", type="eng_float", default=None,
                      help="set frequency to FREQ", metavar="FREQ")
    parser.add_option("-g", "--gain", type="eng_float", default=0.0,
                      help="set gain in dB, [default=%default]")
    parser.add_option("", "--otw-format", type="string", default="sc16",
                      help="set over-the-wire format to USRP [default=%default]")
 #   parser.add_option("", "--peak", type="eng_float", default=1.0,
 #                     help="set peak fraction for sc8 otw format [default=%default]")
    parser.add_option("", "--fullscale", type="eng_float", default=1.0,
                      help="set full scale value for complex32 format [default=%default]")
 
    (options, args) = parser.parse_args ()
    if len(args) != 0:
        parser.print_help()
        raise SystemExit, 1
 
    if options.freq_rx is None:
        parser.print_help()
        sys.stderr.write('You must specify the frequency with -f FREQ\n');
        raise SystemExit, 1
 
    return options
 
if __name__ == '__main__':
    options = get_options()
    tb = tx_mseq_block(options)
 
 
    if options.save is not None:
        tb.run()
        print>>tb.f1, "mseq=[" + str(tb.sink.data()).strip("()") + "];"
        print>>tb.f1, "h=fliplr(conv(kron(mseq,[1 0]),ps));";
        print>>tb.f1, "fid=fopen('" + options.save + ".sig','r');"
        print>>tb.f1, "x=fread(fid,inf,'single');"
        print>>tb.f1, "x=reshape(x,[2 length(x)/2]);"
        print>>tb.f1, "x=x(1,:)+j*x(2,:);"
        print>>tb.f1, "fclose(fid);"
        tb.f1.close
    else:
        try:
            tb.run()
        except KeyboardInterrupt:
            pass
