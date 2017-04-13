import json
from flasky.app import FlaskyApp

app = FlaskyApp()


@app.api(
    endpoint="/api/hello",
    method="GET"
)
async def hello_world(handler):
    handler.write(json.dumps({"hello": "world"}))


@app.scheduler.schedule(interval=5000)
async def scheduled():
    print("hello world 2")

if __name__ == "__main__":
    app.run(8888)
