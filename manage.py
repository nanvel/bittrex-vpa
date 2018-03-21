import asyncio
import sys


if __name__ == '__main__':
    _, command, *arguments = sys.argv

    ioloop = asyncio.get_event_loop()

    if command == 'watch':
        from vpa.watcher import main
        ioloop.run_until_complete(main(markets=arguments[0].split(',')))

    elif command == 'server':
        from vpa.server import main
        main()

    else:
        raise ValueError("Unknown command.")
