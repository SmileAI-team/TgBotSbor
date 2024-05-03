from fastapi import FastAPI

import uvicorn

app = FastAPI()

@app.get("/")
def hellow_index():
    return {
        "message": 'Hellow index !',
    }

@app.get("/items/")
def get_item():
    return [
        "item1",
        "item2"
    ]

@app.get("/item/{item_id}/")
def get_item_id(item_id):
    return {
        "item": {
            "id": item_id,
        },
    }

if __name__ == '__main__':
    uvicorn.run("main:app", reload=True)

