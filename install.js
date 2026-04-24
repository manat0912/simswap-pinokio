module.exports = {
  run: [
    {
      method: "shell.run",
      params: {
        venv: "env",
        path: "app",
        message: [
          "uv pip install -r requirements.txt"
        ]
      }
    },
    {
      method: "script.start",
      params: {
        uri: "torch.js",
        params: {
          venv: "env",
          path: "app"
        }
      }
    },
    {
      method: "fs.download",
      params: {
        uri: "https://github.com/neuralchen/SimSwap/releases/download/1.0/arcface_checkpoint.tar",
        dir: "app/arcface_model"
      }
    },
    {
      method: "fs.download",
      params: {
        uri: "https://github.com/neuralchen/SimSwap/releases/download/1.0/checkpoints.zip",
        dir: "app"
      }
    },
    {
      method: "shell.run",
      params: {
        message: "unzip checkpoints.zip -d checkpoints",
        path: "app"
      }
    },
    {
      method: "shell.run",
      params: {
        message: "rm checkpoints.zip",
        path: "app"
      }
    },
    {
      method: "fs.download",
      params: {
        uri: "https://github.com/facefusion/facefusion-assets/releases/download/models/antelope.zip",
        dir: "app"
      }
    },
    {
      method: "fs.download",
      params: {
        uri: "https://github.com/neuralchen/SimSwap/releases/download/1.0/79999_iter.pth",
        dir: "app/parsing_model/checkpoint"
      }
    },
    {
      method: "shell.run",
      params: {
        message: "unzip antelope.zip -d insightface_func/models/",
        path: "app"
      }
    },
    {
      method: "shell.run",
      params: {
        message: "rm antelope.zip",
        path: "app"
      }
    }
  ]
}
