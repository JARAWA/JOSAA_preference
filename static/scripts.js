document.addEventListener("DOMContentLoaded", function() {
    // Populate dropdown options
    const categories = ["All", "OPEN", "OBC-NCL", "OBC-NCL (PwD)", "EWS", "EWS (PwD)", "SC", "SC (PwD)", "ST", "ST (PwD)"];
    const collegeTypes = ["ALL", "IIT", "NIT", "IIIT", "GFTI"];
    const rounds = ["1", "2", "3", "4", "5", "6"];

    populateDropdown("category", categories);
    populateDropdown("college-type", collegeTypes);
    populateDropdown("round-no", rounds);

    function populateDropdown(id, options) {
        const dropdown = document.getElementById(id);
        options.forEach(option => {
            const opt = document.createElement("option");
            opt.value = option;
            opt.textContent = option;
            dropdown.appendChild(opt);
        });
    }

    // Fetch and populate branches
    fetch("/get_branches")
        .then(response => response.json())
        .then(data => {
            populateDropdown("preferred-branch", data.branches);
        })
        .catch(error => console.error("Error fetching branches:", error));

    // Update probability display
    const probInput = document.getElementById("min-prob");
    const probValue = document.getElementById("prob-value");
    probInput.addEventListener("input", function() {
        probValue.textContent = `${probInput.value}%`;
    });

    // Handle form submission
    document.getElementById("generate-btn").addEventListener("click", function() {
        const jeeRank = document.getElementById("jee-rank").value;
        const category = document.getElementById("category").value;
        const collegeType = document.getElementById("college-type").value;
        const preferredBranch = document.getElementById("preferred-branch").value;
        const roundNo = document.getElementById("round-no").value;
        const minProb = document.getElementById("min-prob").value;

        fetch("/generate_preferences", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                jee_rank: jeeRank,
                category: category,
                college_type: collegeType,
                preferred_branch: preferredBranch,
                round_no: roundNo,
                min_prob: minProb
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                alert(data.error);
            } else {
                displayResults(data);
                document.getElementById("download-btn").style.display = "block";
            }
        })
        .catch(error => console.error("Error:", error));
    });

    function displayResults(data) {
        // Display the table
        const table = document.createElement("table");
        table.innerHTML = `
            <thead>
                <tr>
                    <th>Preference</th>
                    <th>Institute</th>
                    <th>College Type</th>
                    <th>Location</th>
                    <th>Branch</th>
                    <th>Opening Rank</th>
                    <th>Closing Rank</th>
                    <th>Admission Probability (%)</th>
                    <th>Admission Chances</th>
                </tr>
            </thead>
            <tbody>
                ${data.preferences.map(pref => `
                    <tr>
                        <td>${pref.Preference}</td>
                        <td>${pref.Institute}</td>
                        <td>${pref["College Type"]}</td>
                        <td>${pref.Location}</td>
                        <td>${pref.Branch}</td>
                        <td>${pref["Opening Rank"]}</td>
                        <td>${pref["Closing Rank"]}</td>
                        <td>${pref["Admission Probability (%)"]}</td>
                        <td>${pref["Admission Chances"]}</td>
                    </tr>
                `).join("")}
            </tbody>
        `;
        document.getElementById("output-table").innerHTML = "";
        document.getElementById("output-table").appendChild(table);

        // Display the plot
        const plotImg = document.createElement("img");
        plotImg.src = data.plot;
        document.getElementById("prob-plot").innerHTML = "";
        document.getElementById("prob-plot").appendChild(plotImg);
    }

    // Handle download button
    document.getElementById("download-btn").addEventListener("click", function() {
        window.location.href = "/download_excel";
    });
});
