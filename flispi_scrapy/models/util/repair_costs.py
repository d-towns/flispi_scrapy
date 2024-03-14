class RepairCostsSingleton:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(RepairCostsSingleton, cls).__new__(cls)
            cls._instance.init_data()
        return cls._instance

    def init_data(self):
        self.data = {
                    'Electrical Replacement': [2500, 3800],
                    'Plumbing Replacement': 1500,
                    'Water Heater': [1000, 1800],
                    'Furnace Replacement': [3000, 3500],
                    'Duct Installation': 300,
                    'Window Replacement': [500, 600],
                    'Door Replacement': [500, 750],
                    'Drywall Replacement': 12,
                    'Ceiling Replacement': 12,
                    'Floor Covering Replacement': [2.5, 4.5],
                    'Roof Replacement': [350, 550],
                    'Foundation Repairs': 360,
                    'Masonry (Brick) Repairs': 100,
                    'Cut Water Line Replacement': 10000,
                    'Support Beam Repairs': 80,
                    'Support Column Repairs': 250
                }
        self.repairs_mapping = {
                "Clean Out": ["Clean Out"],  # Assume a flat cost or handle specifically
                "HVAC": ["Furnace Replacement", "Duct Installation"],
                "Water Heater": ["Water Heater"],
                "Plumbing": ["Plumbing Replacement"],
                "Electrical": ["Electrical Replacement"],
                "Kitchen Cabinets": ["Kitchen Cabinets"],  # Not in the provided list, may need external data
                "Bathroom": ["Plumbing Replacement"],
                "Clean up and Landscaping": ["Clean up and Landscaping"],
                "Roof": ["Roof Replacement"],
                "Doors": ["Door Replacement"],
                "Windows": ["Window Replacement"],
                "Siding": ["Siding"],  # Not explicitly listed, consider adding a specific entry or use a placeholder cost
                "Garage Repair or Demolition": [
                    "Roof Replacement",
                    "Foundation Repairs",
                    "Support Beam Repairs",
                    "Masonry (Brick) Repairs",
                    "Electrical Replacement",
                    "Drywall Replacement",
                    "Door Replacement",
                    "Window Replacement"
                ],
                "Demolition": [
                    "Cut Water Line Replacement",
                    "Foundation Repairs",
                    "Masonry (Brick) Repairs",
                    "Support Beam Repairs"
                ]
            }
        
    @classmethod
    def get_costs(cls):
        return cls._instance.data
    
    @classmethod
    def get_repair_mappings(cls):
        return cls._instance.repairs_mapping

    @classmethod
    def estimate_repair_costs(cls, property_repairs):
        repair_costs = cls.get_costs()
        repair_mappings = cls.get_repair_mappings()
        estimate = 0
        # For each repair on the property
        for repair in property_repairs:
            specific_repairs = repair_mappings.get(repair, [])

            # Handle unspecified or special cases
            if specific_repairs is None:
                # Implement special logic for unmapped or flat-rate repairs
                continue

            for specific in specific_repairs:
                # Assuming internal repairs, adjust if needed for external repairs
                cost = repair_costs['internal'].get(specific)
                if isinstance(cost, list):
                    # If there's a range, take the average or one of the ends as required
                    estimate += sum(cost) / len(cost)
                elif isinstance(cost, dict):
                    # Sum average costs of all detailed options
                    detailed_costs = cost.values()
                    detailed_estimates = [
                        sum(value) / len(value) if isinstance(value, list) else value
                        for value in detailed_costs
                    ]
                    estimate += sum(detailed_estimates) / len(detailed_estimates)
                else:
                    estimate += cost

        return estimate
