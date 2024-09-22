import pandas as pd
import numpy as np
import numpy_financial as npf
import openpyxl

class CREAcquisitionModel:
    def __init__(self, excel_file_path):
        self.excel_file_path = excel_file_path
        self.load_data_from_excel()

    def load_data_from_excel(self):
        """Load data from Excel file"""
        try:
            df = pd.read_excel(self.excel_file_path)
            
            # Assign values from Excel to class attributes
            self.purchase_price = df['Value'].loc[df['Parameter'] == 'Purchase Price'].values[0]
            self.annual_rent = df['Value'].loc[df['Parameter'] == 'Annual Rent'].values[0]
            self.occupancy_rate = df['Value'].loc[df['Parameter'] == 'Occupancy Rate'].values[0]
            self.operating_expenses = df['Value'].loc[df['Parameter'] == 'Operating Expenses'].values[0]
            self.capex_reserve = df['Value'].loc[df['Parameter'] == 'CapEx Reserve'].values[0]
            self.loan_amount = df['Value'].loc[df['Parameter'] == 'Loan Amount'].values[0]
            self.interest_rate = df['Value'].loc[df['Parameter'] == 'Interest Rate'].values[0]
            self.loan_term = df['Value'].loc[df['Parameter'] == 'Loan Term'].values[0]
            self.holding_period = df['Value'].loc[df['Parameter'] == 'Holding Period'].values[0]
            self.federal_tax_rate = df['Value'].loc[df['Parameter'] == 'Federal Tax Rate'].values[0]
            self.state_tax_rate = df['Value'].loc[df['Parameter'] == 'State Tax Rate'].values[0]
            self.local_tax_rate = df['Value'].loc[df['Parameter'] == 'Local Tax Rate'].values[0]
            self.depreciation_period = df['Value'].loc[df['Parameter'] == 'Depreciation Period'].values[0]
            self.target_irr = df['Value'].loc[df['Parameter'] == 'Target IRR'].values[0]
            self.exit_cap_rate = df['Value'].loc[df['Parameter'] == 'Exit Cap Rate'].values[0]

        except Exception as e:
            print(f"Error loading data from Excel: {e}")
            raise

    def calculate_noi(self):
        """Calculate Net Operating Income"""
        effective_gross_income = self.annual_rent * self.occupancy_rate
        return effective_gross_income - self.operating_expenses

    def calculate_debt_service(self):
        """Calculate annual debt service"""
        monthly_rate = self.interest_rate / 12
        num_payments = self.loan_term * 12
        return npf.pmt(monthly_rate, num_payments, self.loan_amount) * 12

    def calculate_depreciation(self):
        """Calculate annual depreciation"""
        depreciable_basis = self.purchase_price * 0.8  # Assuming 80% of purchase price is depreciable
        return depreciable_basis / self.depreciation_period

    def calculate_taxable_income(self):
        """Calculate taxable income"""
        noi = self.calculate_noi()
        interest_expense = self.calculate_debt_service() * (self.interest_rate / (self.interest_rate + 1/self.loan_term))
        depreciation = self.calculate_depreciation()
        return noi - interest_expense - depreciation

    def calculate_taxes(self):
        """Calculate total taxes"""
        taxable_income = self.calculate_taxable_income()
        federal_tax = taxable_income * self.federal_tax_rate
        state_tax = taxable_income * self.state_tax_rate
        local_tax = taxable_income * self.local_tax_rate
        return federal_tax + state_tax + local_tax

    def calculate_after_tax_cash_flow(self):
        """Calculate after-tax cash flow"""
        pre_tax_cash_flow = self.calculate_noi() - self.calculate_debt_service() - self.capex_reserve
        taxes = self.calculate_taxes()
        return pre_tax_cash_flow - taxes

    def calculate_cap_rate(self):
        """Calculate capitalization rate"""
        return self.calculate_noi() / self.purchase_price

    def calculate_cash_on_cash_return(self):
        """Calculate after-tax cash-on-cash return"""
        equity_investment = self.purchase_price - self.loan_amount
        annual_after_tax_cash_flow = self.calculate_after_tax_cash_flow()
        return annual_after_tax_cash_flow / equity_investment

    def calculate_irr(self):
        """Calculate after-tax Internal Rate of Return"""
        equity_investment = self.purchase_price - self.loan_amount
        cash_flows = [-equity_investment]
        
        for _ in range(int(self.holding_period)):
            cash_flows.append(self.calculate_after_tax_cash_flow())
        
        exit_noi = self.calculate_noi() * (1 + 0.02) ** self.holding_period  # Assume 2% annual NOI growth
        exit_value = exit_noi / self.exit_cap_rate
        remaining_loan_balance = npf.fv(self.interest_rate / 12, self.holding_period * 12, -npf.pmt(self.interest_rate / 12, self.loan_term * 12, self.loan_amount), self.loan_amount)
        net_exit_proceeds = exit_value - remaining_loan_balance
        
        # Calculate capital gains tax
        capital_gain = exit_value - self.purchase_price
        depreciation_recapture = self.calculate_depreciation() * self.holding_period
        capital_gains_tax = (capital_gain * 0.20) + (depreciation_recapture * 0.25)  # Assume 20% long-term capital gains rate and 25% depreciation recapture rate
        
        cash_flows[-1] += net_exit_proceeds - capital_gains_tax
        
        return npf.irr(cash_flows)

    def evaluate_acquisition(self):
        """Evaluate if the property is worth acquiring"""
        cap_rate = self.calculate_cap_rate()
        coc_return = self.calculate_cash_on_cash_return()
        irr = self.calculate_irr()
        
        evaluation = {
            "Cap Rate": cap_rate,
            "After-Tax Cash-on-Cash Return": coc_return,
            "After-Tax IRR": irr,
            "Annual After-Tax Cash Flow": self.calculate_after_tax_cash_flow(),
            "Is Worth Acquiring": irr > self.target_irr
        }
        
        return evaluation

def main():
    # Example
    excel_file_path = 'path/to/your/excel/file.xlsx'
    model = CREAcquisitionModel(excel_file_path)

    evaluation = model.evaluate_acquisition()
    
    print("Acquisition Evaluation (After-Tax):")
    for key, value in evaluation.items():
        if isinstance(value, float):
            print(f"{key}: {value:.2%}")
        else:
            print(f"{key}: {value}")

if __name__ == "__main__":
    main()
