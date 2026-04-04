// Dummy Data (In future, aap ise Django Database se la sakte hain)
const mockData = [
    { title: "Django Tutorial for Beginners", url: "https://docs.djangoproject.com", desc: "Django is a high-level Python web framework that encourages rapid development." },
    { title: "Bootstrap 5 Styling Guide", url: "https://getbootstrap.com", desc: "Powerful, extensible, and feature-packed frontend toolkit." },
    { title: "Python Programming in Hindi", url: "#", desc: "Python ek bahut hi aasan aur powerful programming language hai." }
];

document.addEventListener("DOMContentLoaded", function() {
    const params = new URLSearchParams(window.location.search);
    const query = params.get('q');
    const container = document.getElementById("results-container");

    if (query) {
        // Query ko input box mein bhi dikhao
        if(document.getElementById("search-input")) {
            document.getElementById("search-input").value = query;
        }

        // Filter results
        const results = mockData.filter(item => 
            item.title.toLowerCase().includes(query.toLowerCase()) || 
            item.desc.toLowerCase().includes(query.toLowerCase())
        );

        // Display results
        if (results.length > 0) {
            container.innerHTML = results.map(item => `
                <div class="result-card">
                    <small class="text-success">${item.url}</small>
                    <a href="${item.url}"><h3>${item.title}</h3></a>
                    <p class="text-dark">${item.desc}</p>
                </div>
            `).join('');
        } else {
            container.innerHTML = `<div class="mt-5 text-center text-muted"><h3>"${query}" ke liye kuch nahi mila!</h3></div>`;
        }
    }
});