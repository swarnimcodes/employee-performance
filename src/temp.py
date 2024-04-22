from pydantic import BaseModel, HttpUrl


class URLStructure(BaseModel):
    url: HttpUrl


# Example usage
if __name__ == "__main__":
    # # Valid URL
    # valid_url = URLStructure(url="https://www.example.com")
    # print(valid_url)

    # Invalid URL
    try:
        invalid_url = URLStructure(url="http://localhost:8090")
        print(invalid_url)
    except ValueError as e:
        print(e)
