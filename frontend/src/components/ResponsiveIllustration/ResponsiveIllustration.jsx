import './ResponsiveIllustration.css'

import illustration from "./assets/images/illustration.png"
import motto from "./assets/images/motto.svg"

export default function ResponsiveIllustration ()
{
        return <div className='ResponsiveIllustration-right'>
                <img className='ResponsiveIllustration_right-concept' src={illustration} alt="Design" />
                <img className='ResponsiveIllustration_right-motto' src={motto} alt="The Right Path Starts With The Right Information" />
        </div>
}
