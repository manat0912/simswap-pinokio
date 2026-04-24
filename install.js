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
      when: "{{!exists('app/arcface_model/arcface_checkpoint.tar')}}",
      method: "fs.download",
      params: {
        uri: "https://github.com/neuralchen/SimSwap/releases/download/1.0/arcface_checkpoint.tar",
        dir: "app/arcface_model"
      }
    },
    {
      when: "{{!exists('app/checkpoints')}}",
      method: "fs.download",
      params: {
        uri: "https://github.com/neuralchen/SimSwap/releases/download/1.0/checkpoints.zip",
        dir: "app"
      }
    },
    {
      when: "{{!exists('app/checkpoints') && exists('app/checkpoints.zip')}}",
      method: "shell.run",
      params: {
        message: "unzip checkpoints.zip -d checkpoints",
        path: "app"
      }
    },
    {
      when: "{{exists('app/checkpoints.zip')}}",
      method: "shell.run",
      params: {
        message: "rm checkpoints.zip",
        path: "app"
      }
    },
    {
      when: "{{!exists('app/insightface_func/models/antelope')}}",
      method: "fs.download",
      params: {
        uri: "https://huggingface.co/haikumonster/antelope/resolve/main/antelope.zip",
        dir: "app"
      }
    },
    {
      when: "{{!exists('app/parsing_model/checkpoint/79999_iter.pth')}}",
      method: "fs.download",
      params: {
        uri: "https://github.com/neuralchen/SimSwap/releases/download/1.0/79999_iter.pth",
        dir: "app/parsing_model/checkpoint"
      }
    },
    {
      when: "{{!exists('app/insightface_func/models/antelope') && exists('app/antelope.zip')}}",
      method: "shell.run",
      params: {
        message: "unzip antelope.zip -d insightface_func/models/",
        path: "app"
      }
    },
    {
      when: "{{exists('app/antelope.zip')}}",
      method: "shell.run",
      params: {
        message: "rm antelope.zip",
        path: "app"
      }
    }
  ]
}
