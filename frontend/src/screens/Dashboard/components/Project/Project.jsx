import './Project.css'

import tripleDots from "../../../../assets/images/dashboard-tripleDots.svg"
import calendar from "../../../../assets/images/dashboard-calendar.svg"

export default function Project (props) {
        return  <button type="button" className='Dashboard_project'>
                <div className='Dashboard_project_title'>
                        {props?.title}
                        <img src={tripleDots} />
                </div>
                <div className='Dashboard_project_description'>{props?.children}</div>
                <div className='Dashboard_project_footer'>
                        <div className='Dashboard_project_date'>
                                <img src={calendar} />
                                {props?.date}
                        </div>
                        <div
                                className='Dashboard_project_label'
                                style={{background: props?.status === "Completed" ? "#01A89A" : "#FF671F"}}
                        >
                                {props?.status}
                        </div>
                </div>
        </button>
}