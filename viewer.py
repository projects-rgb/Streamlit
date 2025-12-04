from flask import Flask, request, render_template_string
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <script type="module" src="{{ module_url }}"></script>
</head>
<body style="margin:0; padding:0; overflow:hidden;">

<div id="viz_container" style="width:100vw; height:100vh;"></div>

<script type="module">
async function loadViz() {

    console.log("Loading Tableau viz...");

    const container = document.getElementById("viz_container");
    container.innerHTML = "";

    const viz = document.createElement("tableau-viz");
    viz.src = "{{ view_url }}";
    viz.toolbar = "bottom";
    viz.style.width = "100%";
    viz.style.height = "100vh";

    // Auto-refresh JWT token
    viz.token = async () => {
        const r = await fetch("http://127.0.0.1:5001/new_jwt", { cache: "no-store" });
        const j = await r.json();
        return j.token;
    };

    container.appendChild(viz);
}

loadViz();
</script>

</body>
</html>
"""

@app.get("/view")
def view():
    view_url = request.args.get("url")
    module_url = "https://prod-in-a.online.tableau.com/javascripts/api/tableau.embedding.3.latest.min.js"
    return render_template_string(TEMPLATE, view_url=view_url, module_url=module_url)

if __name__ == "__main__":
    app.run(port=8502)
