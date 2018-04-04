#!/usr/bin/env python

"""Simple HTTP Echo Server."""
import argparse
import errno
import time
import queue
import multiprocessing
import logging
import select
import socket
import threading

class _Worker(object):

    """Abstract base class for simple workers."""

    def __init__(self, tasks_queue, stop_event, delay=0.1):
        super(_Worker, self).__init__()
        self._queue = tasks_queue
        self._stop = stop_event
        self._delay = delay
        
        self._name = self.__class__.__name__
        self._logger = logging.getLogger(self._name)

        self.run()

    def _get_task(self):
        """Retrieves a task from the queue."""
        while not self._stop.is_set():
            try:
                task = self._queue.get(block=False)
                if task:
                    return task
            except queue.Empty:
                time.sleep(self._delay)

    def _task_done(self, task, result):
        """What to execute after successfully finished processing a task."""
        pass

    def _task_fail(self, task, exc):
        """What to do when the program fails processing a task."""
        pass

    def _process(self, task):
        """Override this with your custom worker logic."""
        pass

    def run(self):
        """Worker able to retrieve and process tasks."""
        self._logger.debug("The worker is starting...")
        while not self._stop.is_set():
            task = self._get_task()
            try:
                result = self._process(task)
            except Exception as exc:
                self._task_fail(task, exc)
            else:
                self._task_done(task, result)


class _Daemon(object):

    """Abstract base class for simple daemons."""

    def __init__(self, delay=1, workers=7):
        """Setup a new instance."""
        self._delay = delay
        self._workers_count = workers
        self._workers = list()
        self._manager = None
        self._queue = queue.Queue()
        self._stop = threading.Event()

        self._name = self.__class__.__name__
        self._logger = logging.getLogger(self._name)

    def _start_worker(self):
        """Creates a new worker."""
        pass

    def _task_generator(self):
        """Override this with your custom task generator."""
        pass

    def manage_workers(self):
        """Maintain a desired number of workers up."""
        while not self._stop.is_set():
            for worker in self._workers[:]:
                if not worker.is_alive():
                    self._workers.remove(worker)

            if len(self._workers) == self._workers_count:
                time.sleep(self._delay)
                continue

            worker = self._start_worker()
            self._workers.append(worker)

    def _interrupted(self):
        """Mark the processing as stopped."""
        self._stop.set()

    def _put_task(self, task):
        """Adds a task to the queue."""
        self._queue.put(task)

    def _prologue(self):
        """Start a parallel supervisor."""
        self._manager = threading.Thread(target=self.manage_workers)
        self._manager.start()

    def _epilogue(self):
        """Wait for that supervisor and its workers."""
        self._logger.info("The server is shuting down...")
        if self._manager:
            self._logger.debug("Waiting for the management thread...")
            self._manager.join()

        self._logger.debug("Waiting for workers...")
        for worker in self._workers:
            if worker.is_alive():
                worker.join()

    def start(self):
        """Starts a series of workers and processes incoming tasks."""
        self._prologue()
        while not self._stop.is_set():
            try:
                for task in self._task_generator():
                    self._put_task(task)
            except KeyboardInterrupt:
                self._interrupted()
                break
        self._epilogue()


class HTTPWorker(_Worker):

    """Simple HTTP echo worker."""

    def _get_response(self, content, response_code="200 OK"):
        headers = {
            "Date": time.strftime("%a, %d %b %Y %H:%M:%S", time.localtime()),
            "Server": self._name,
            "Connection": "close",
            "X-Laborator": "Tehnologii Web",
            "Content-Length": len(content),
            "Content-Type": "text/plain",
        }
        output = ["HTTP/1.1 {response}".format(response=response_code)]
        for key, value in headers.items():
            output.append("{key}: {value}".format(key=key.title(),
                                                  value=value))
        output.append("\n")
        output.append(content)
        return "\n".join(output)

    def _task_done(self, task, result):
        """Send the result to the client."""
        response = self._get_response(result, "200 OK")
        task.sendall(response.encode())
        task.close()

    def _task_fail(self, task, exc):
        """Send an error to the client"""
        if not task:
            return
        task.close()

    def _process(self, task):
        """Receive the information from the client."""
        request = []
        while True:
            chunk = task.recv(1024)
            request.append(chunk.decode())
            if len(chunk) < 1024:
                break

        return "".join(request)


class HTTPServer(_Daemon):

    """Simple HTTP Server."""

    def __init__(self, host, port, backlog=7):
        super(HTTPServer, self).__init__()
        self._port = port
        self._host = host
        self._backlog = backlog
        self._socket = None

    def _start_worker(self):
        """Start a new HTTP Worker."""
        self._logger.info("Starting a new worker...")
        worker = threading.Thread(target=HTTPWorker,
                                  args=(self._queue, self._stop))
        worker.setDaemon(True)
        worker.start()
        return worker

    def _task_generator(self):
        """Listen for new connection and pass them to the workers."""
        read_list, write_list, error_list = [self._socket], [], []
        while not self._stop.is_set():
            readables, _, _ = select.select(read_list, write_list, error_list)
            if self._socket not in readables:
                continue
            try:
                connection, _ = self._socket.accept()
            except IOError as exc:
                code, _ = exc.args
                if code == errno.EINTR:
                    continue
            yield connection

    def _prologue(self):
        """Setup the socket."""
        self._logger.info("The HTTP server is starting...")
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._socket.setblocking(0)

        try:
            self._socket.bind((self._host, self._port))
            self._socket.listen(self._backlog)
        except OSError as exc:
            self._logger.error("Failed to start server: %s", exc)
            self._stop.set()
            return

        self._logger.info("The server is listening on %s:%s",
                          self._host, self._port)
        super(HTTPServer, self)._prologue()


def main():
    """The entrypoint of the current script."""
    logging.basicConfig(level=logging.DEBUG)
    server = HTTPServer(host="0.0.0.0", port=8080)
    server.start()


if __name__ == "__main__":
    main()
