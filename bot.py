import argparse
import os
from src.pennyworth import Pennyworth
    

def main():
    p = argparse.ArgumentParser(
        description=Pennyworth.__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument(
        '-c',
        '--config',
        default='config.yml',
        help="path to a config file or just config's filename")
    args = p.parse_args()

    script_path = os.path.dirname(os.path.realpath(__file__))
    config_file_path = None
    if os.path.isabs(args.config):
        config_file_path = args.config
    else:
        config_file_path = os.path.join(script_path, args.config)

    bot = Pennyworth(config_file_path)
    bot.start()


if __name__ == '__main__':
    main()
