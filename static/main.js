let searchbar = document.querySelector('#stocksearch');

searchbar.addEventListener('keydown', function () {
let lastMove = 0
    // do nothing if last move was less than 40 ms ago
    if (Date.now() - lastMove > 400) {
        // https://thingproxy.freeboard.io/fetch/ CORS proxy used. Yahoo endpoint does not allow frontend requests.
        let url = 'https://thingproxy.freeboard.io/fetch/https://query2.finance.yahoo.com/v1/finance/search'
        let search_query = searchbar.value
        let params = `?q=${search_query}&quotesCount=7&newsCount=0`
        let search_url = url + params
        companies = preload(search_url);
        lastUpdate = Date.now();
    }
});

async function preload(url) {
    document.querySelector('#test_list').innerHTML = ""
    const response = await fetch(url);
    const data = await response.json();
    companies = data["quotes"];
    console.log(companies)
    for (company in companies) {
        console.log(company)
        document.querySelector('#test_list').innerHTML += 
            `<li class="list-group-item">
                <div>${companies[company]["symbol"]}
                ${companies[company]["shortname"]}
                ${companies[company]["exchange"]}</div>
            </li>`
    }
}

