var fs = require('fs');
var path = require('path');

function createSimplePNG(width, height) {
    var png = [];
    png.push(0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A);

    function crc32(data) {
        var crc = 0xFFFFFFFF;
        var table = [];
        for (var i = 0; i < 256; i++) {
            var c = i;
            for (var j = 0; j < 8; j++) {
                c = (c & 1) ? (0xEDB88320 ^ (c >>> 1)) : (c >>> 1);
            }
            table[i] = c;
        }
        for (var k = 0; k < data.length; k++) {
            crc = table[(crc ^ data[k]) & 0xFF] ^ (crc >>> 8);
        }
        return (crc ^ 0xFFFFFFFF) >>> 0;
    }

    function addChunk(type, data) {
        var length = [
            (data.length >>> 24) & 0xFF,
            (data.length >>> 16) & 0xFF,
            (data.length >>> 8) & 0xFF,
            data.length & 0xFF
        ];
        var typeBytes = type.split('').map(function(c) { return c.charCodeAt(0); });
        var crcData = typeBytes.concat(data);
        var crc = crc32(crcData);
        var crcBytes = [
            (crc >>> 24) & 0xFF,
            (crc >>> 16) & 0xFF,
            (crc >>> 8) & 0xFF,
            crc & 0xFF
        ];
        png.push.apply(png, length);
        png.push.apply(png, typeBytes);
        png.push.apply(png, data);
        png.push.apply(png, crcBytes);
    }

    var ihdrData = [
        (width >>> 24) & 0xFF, (width >>> 16) & 0xFF, (width >>> 8) & 0xFF, width & 0xFF,
        (height >>> 24) & 0xFF, (height >>> 16) & 0xFF, (height >>> 8) & 0xFF, height & 0xFF,
        8, 6, 0, 0, 0
    ];
    addChunk('IHDR', ihdrData);

    var rawData = [];
    var r = 22, g = 93, b = 255;
    for (var y = 0; y < height; y++) {
        rawData.push(0);
        for (var x = 0; x < width; x++) {
            rawData.push(r, g, b);
            rawData.push(255);
        }
    }

    var zlib = require('zlib');
    var compressed = zlib.deflateSync(new Buffer(rawData));
    var compressedArray = [];
    for (var i = 0; i < compressed.length; i++) {
        compressedArray.push(compressed[i]);
    }
    addChunk('IDAT', compressedArray);
    addChunk('IEND', []);

    return new Buffer(png);
}

var sizes = [48, 72, 96, 144, 192, 512];
var outputDir = path.join(__dirname, '../assets/icons/pwa');

if (!fs.existsSync(outputDir)) {
    fs.mkdirSync(outputDir, { recursive: true });
}

sizes.forEach(function(size) {
    var png = createSimplePNG(size, size);
    var filePath = path.join(outputDir, 'icon-' + size + 'x' + size + '.png');
    fs.writeFileSync(filePath, png);
    console.log('Created:', filePath);
});

console.log('All PWA icons generated successfully!');