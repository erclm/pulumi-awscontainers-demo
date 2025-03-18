'use strict';

const express = require('express');

// Constants
const PORT = 80;
const HOST = '0.0.0.0';

const MESSAGE = process.env.APP_MESSAGE || 'Hello World';

// App
const app = express();
app.get('/', (req, res) => {
  res.send(`${MESSAGE}`);
});

app.listen(PORT, HOST);
console.log(`Running on http://${HOST}:${PORT}`);