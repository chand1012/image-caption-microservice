# Image Captioning Microservice

A microservice that adds captions to images at specified coordinates using Docker, Python, FastAPI, and Pillow. This service allows you to overlay text on images with customizable fonts, sizes, colors, and borders.

## Table of Contents

- [Features](#features)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Project Structure](#project-structure)
- [Usage](#usage)
  - [API Endpoint](#api-endpoint)
  - [Request Parameters](#request-parameters)
  - [Response Format](#response-format)
  - [Example Request](#example-request)
- [Testing](#testing)
- [Fonts and Licensing](#fonts-and-licensing)
- [Best Practices Implemented](#best-practices-implemented)
- [Contributing](#contributing)
- [License](#license)

## Features

- **Add Captions to Images**: Overlay text onto images at specific coordinates.
- **Multiple Captions**: Support for multiple text boxes per image.
- **Customizable Text**:
  - Font: Choose between Arial and Impact.
  - Font Size: Specify a size or let the service maximize the text within the box.
  - Color and Border: Customize text color and border with hex codes or standard CSS color names.
- **Text Wrapping**: Automatically wraps text to fit within the box dimensions.
- **Image Support**: Accepts images via URL or base64 encoding.
- **Output Formats**: Returns images as base64-encoded strings or image files in JPEG or PNG formats.

## Prerequisites

- **Docker**: Ensure Docker is installed on your machine.
- **Python 3.9+**: The service uses Python 3.9.

## Installation

Clone the repository and navigate to the project directory:

```bash
git clone https://github.com/yourusername/image-captioning-microservice.git
cd image-captioning-microservice
```

Build the Docker image:

```bash
docker build -t image-caption-service .
```

Run the Docker container:

```bash
docker run -p 8080:80 image-caption-service
```


## Project Structure

```
image-captioning-microservice/
├── app/
│   ├── main.py
│   ├── requirements.txt
├── fonts/
│   ├── arial.ttf
│   ├── impact.ttf
├── Dockerfile
├── README.md
```

- **app/**: Contains the application code.
  - **main.py**: The main FastAPI application.
  - **requirements.txt**: Dependencies.
- **fonts/**: Contains font files.
- **Dockerfile**: Docker configuration.
- **README.md**: Project documentation.

## Usage

### API Endpoint

- **URL**: `http://localhost:8080/`
- **Method**: `POST`
- **Content-Type**: `application/json`

### Request Parameters

The API accepts a JSON payload with the following structure:

```json
{
  "img": "string",            // Required: URL or base64-encoded image
  "boxes": [                  // Required: List of boxes
    {
      "text": "string",             // Required: Text to overlay
      "x": integer,                 // Required: X-coordinate
      "y": integer,                 // Required: Y-coordinate
      "w": integer,                 // Required: Width of the box
      "h": integer,                 // Required: Height of the box
      "font": "string",             // Optional: "arial" or "impact" (default: "arial")
      "fontsize": integer,          // Optional: Font size (auto-calculated if omitted)
      "color": "string",            // Optional: Text color (hex code or CSS color name)
      "border": "string"            // Optional: Border color (hex code or CSS color name)
    }
    // Add more boxes as needed
  ],
  "image_format": "string"     // Optional: Output format ("b64/jpeg", "b64/png", "image/jpeg", "image/png")
}
```

#### Field Descriptions

- **img**: A URL to an image or a base64-encoded image string.
- **boxes**: An array of box objects containing text and styling information.
  - **text**: The caption text to be added to the image.
  - **x**, **y**: Coordinates where the text box starts.
  - **w**, **h**: Width and height of the text box.
  - **font**: Choose between `"arial"` or `"impact"`. Default is `"arial"`.
  - **fontsize**: The size of the font. If omitted, the service calculates the maximum size that fits.
  - **color**: Text color. Accepts hex codes (e.g., `"#FFFFFF"`) or CSS color names (e.g., `"white"`).
  - **border**: Border (stroke) color for the text. Accepts the same formats as `color`.
- **image_format**: Specifies the output format. Defaults to the same format as the input image.

### Response Format

Depending on the `image_format`, the API returns:

- **Base64-encoded image**: If `image_format` starts with `"b64/"`, the response is JSON:
  ```json
  {
    "img": "base64-encoded image string"
  }
  ```
- **Image file**: If `image_format` starts with `"image/"`, the response is the raw image file with appropriate headers.

### Example Request

#### Python Script Example

```python
import base64
import requests

# Image URL or base64-encoded image
image_url = "https://example.com/path/to/image.jpg"

payload = {
    "img": image_url,
    "boxes": [
        {
            "text": "Hello World!",
            "x": 50,
            "y": 100,
            "w": 300,
            "h": 100,
            "font": "impact",
            "fontsize": 40,
            "color": "#FF5733",
            "border": "black"
        },
        {
            "text": "This text wraps into multiple lines within the specified box dimensions.",
            "x": 50,
            "y": 250,
            "w": 300,
            "h": 150,
            "font": "arial"
            # fontsize omitted to auto-calculate
        }
    ],
    "image_format": "b64/jpeg"
}

response = requests.post("http://localhost:8080/", json=payload)

if response.status_code == 200:
    result = response.json()
    image_data = base64.b64decode(result['img'])
    with open("output_image.jpg", "wb") as out_file:
        out_file.write(image_data)
    print("Image saved successfully.")
else:
    print(f"Error {response.status_code}: {response.text}")
```

## Testing

You can test the API using tools like **Postman** or **cURL**.

### Using cURL

```bash
curl -X POST "http://localhost:8080/" \
     -H "Content-Type: application/json" \
     -d '{
           "img": "https://example.com/image.jpg",
           "boxes": [
             {
               "text": "Sample Text",
               "x": 50,
               "y": 100,
               "w": 300,
               "h": 100,
               "font": "arial",
               "fontsize": 30,
               "color": "blue",
               "border": "#FF0000"
             }
           ],
           "image_format": "image/png"
         }' --output output_image.png
```

This command sends a POST request to the API and saves the resulting image as `output_image.png`.

<!-- ## Fonts and Licensing

### Included Fonts

- **Arial**
- **Impact**

**Note**: The Arial and Impact fonts are proprietary and may require proper licensing for distribution. Ensure you have the rights to use these fonts in your project.

### Open-Source Alternatives

If licensing is a concern, consider replacing the proprietary fonts with open-source alternatives:

- **Arial Alternative**: [Liberation Sans](https://github.com/liberationfonts/liberation-fonts)
- **Impact Alternative**: [Anton](https://fonts.google.com/specimen/Anton)

Update the font files in the `fonts/` directory and adjust the font paths in `main.py` accordingly.
 -->

## Best Practices Implemented

- **Validation with Pydantic**: Ensures the request payload is structured correctly.
- **Error Handling**: Provides meaningful HTTP status codes and error messages.
- **Efficient Font Size Calculation**: Uses a binary search to maximize font size within box dimensions.
- **Security Measures**:
  - Validates image URLs to prevent SSRF (Server-Side Request Forgery) attacks.
  - Sets timeouts for external HTTP requests.
  - Limits allowed image formats to `PNG` and `JPEG`.
  - Sanitizes color inputs by relying on Pillow's internal validation.


## Contributing

Contributions are welcome! Feel free to submit a pull request or open an issue.

### Steps to Contribute

1. Fork the repository.
2. Create a new branch: `git checkout -b feature/YourFeature`.
3. Commit your changes: `git commit -am 'Add new feature'`.
4. Push to the branch: `git push origin feature/YourFeature`.
5. Open a pull request.

## License

This project is licensed under the **MIT License**.
