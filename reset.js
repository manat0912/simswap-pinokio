module.exports = {
  run: [
    {
      method: "fs.rm",
      params: {
        path: "app/env"
      }
    },
    {
      method: "fs.rm",
      params: {
        path: "app/arcface_model"
      }
    },
    {
      method: "fs.rm",
      params: {
        path: "app/checkpoints"
      }
    },
    {
      method: "fs.rm",
      params: {
        path: "app/insightface_func/models"
      }
    },
    {
      method: "fs.rm",
      params: {
        path: "app/parsing_model/checkpoint"
      }
    }
  ]
}
