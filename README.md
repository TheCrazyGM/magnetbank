# Instructions

```sh
mongo torrents --eval 'db.torrents.createIndex({hash: "text", file_name: "text", submitted_by: "text"})'
```
