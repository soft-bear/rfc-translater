
import sys
from src.fetch_rfc import fetch_rfc, RFCNotFound
from src.trans_rfc import trans_rfc
from src.make_html import make_html
from src.fetch_index import diff_remote_and_local_index

def main(rfc_number):
    print('RFC %d:' % rfc_number)

    try:
        fetch_rfc(rfc_number)
    except RFCNotFound as e:
        print('Exception: RFCNotFound!')
        filename = "html/rfc%d-not-found.html" % rfc_number
        with open(filename, "w") as f:
            f.write('')
        return

    trans_rfc(rfc_number)
    if ENDLESS_MODE: return
    make_html(rfc_number)

def continuous_main(maximum=100, begin=None, end=None):
    if begin and end:
        numbers = list(range(begin, end+1))
    else:
        numbers = list(diff_remote_and_local_index())
    for rfc_number in numbers[:maximum]:
        main(rfc_number)

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--rfc', type=int, help='RFC number')
    parser.add_argument('--fetch', action='store_true', help='only fetch RFC')
    parser.add_argument('--trans', action='store_true', help='only translate')
    parser.add_argument('--make', action='store_true', help='only make HTML')
    parser.add_argument('--continuous', action='store_true', help='continuous process')
    parser.add_argument('--max', type=int, help='continuous: max time')
    parser.add_argument('--begin', type=int, help='continuous: begin rfc number')
    parser.add_argument('--end', type=int, help='continuous: end rfc number')
    parser.add_argument('--endless-mode',
        dest='endless_mode', action='store_true', help='continuous: end rfc number')
    args = parser.parse_args()

    global ENDLESS_MODE
    ENDLESS_MODE = args.endless_mode

    if args.fetch and args.rfc:
        fetch_rfc(args.rfc)
    elif args.trans and args.rfc:
        trans_rfc(args.rfc)
    elif args.make and args.rfc:
        make_html(args.rfc)

    elif not args.continuous and args.rfc:
        main(args.rfc)
    else:
        continuous_main(maximum=args.max, begin=args.begin, end=args.end)
