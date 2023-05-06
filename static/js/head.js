// Define an arrow function to get dynamic global properties
const getDynamicGlobalProperties = async () => {
  const response = await fetch("https://api.hive.blog", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      jsonrpc: "2.0",
      method: "condenser_api.get_dynamic_global_properties",
      params: [],
      id: 1,
    }),
  });

  const data = await response.json();
  return data.result.head_block_number;
};

// Call the arrow function to get the head block number and update the HTML element
$(document).ready(async () => {
  const headBlockNumber = await getDynamicGlobalProperties();
  $("#head-block-number").text(headBlockNumber);
});
