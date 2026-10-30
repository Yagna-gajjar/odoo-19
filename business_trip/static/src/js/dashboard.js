/** @odoo-module **/

fetch('/trip/data', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json'
    },
    body: JSON.stringify({
        jsonrpc: '2.0',
        method: 'call',
        params: {},
        id: 1
    })
})
.then(response => {
    console.log("HTTP Status:", response.status);
    return response.json();
})
.then(data => {
    console.log("Received Data:", data);
})
.catch(error => {
    console.error("Fetch Error:", error);
});