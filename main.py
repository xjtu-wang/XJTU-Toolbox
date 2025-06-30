import argparse

from getassess import main as getassess_main
from getchair import main as getchair_main
from getchair_request import main as getchair_request_main
from getcourse import main as getcourse_main

def main():

    parser = argparse.ArgumentParser(
        description="这是一个主控程序，用于调用不同的功能模块。",
        epilog="使用 'python main.py <功能> -h' 来查看具体功能的帮助信息。"
    )

    parser.add_argument(
        'feature',
        choices=['1', '2', '3','4'],
        help="选择要执行的功能: '1' for 自动评教, '2' for 快速抢座, '3' for 可视化抢座, '4' for 抢课"
    )

    args = parser.parse_args()

    print(f"接收到指令，准备执行功能 '{args.feature}'...")

    if args.feature == '1':
        getassess_main()
    elif args.feature == '2':
        getchair_main()
    elif args.feature == '3':
        getchair_request_main()
    elif args.feature == '4':
        getcourse_main()
    else:
        print(f"错误：未知的功能 '{args.feature}'")


if __name__ == '__main__':
    main()